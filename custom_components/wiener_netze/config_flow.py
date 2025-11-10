"""Config flow for Wiener Netze Smart Meter integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    WienerNetzeApiClient,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
    format_meter_point_address,
)
from .const import (
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class WienerNetzeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wiener Netze Smart Meter."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_client: WienerNetzeApiClient | None = None
        self._credentials: dict[str, Any] = {}
        self._meter_points: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store credentials
            self._credentials = user_input

            # Create API client
            session = async_get_clientsession(self.hass)
            self._api_client = WienerNetzeApiClient(
                session=session,
                client_id=user_input[CONF_CLIENT_ID],
                client_secret=user_input[CONF_CLIENT_SECRET],
                api_key=user_input[CONF_API_KEY],
            )

            # Test authentication
            try:
                await self._api_client.authenticate()
                _LOGGER.info("Authentication successful")

                # Fetch meter points
                self._meter_points = await self._api_client.get_meter_points()

                if not self._meter_points:
                    errors["base"] = "no_meter_points"
                else:
                    # Multiple meter points: show selection
                    if len(self._meter_points) > 1:
                        return await self.async_step_meter_point()

                    # Single meter point: use directly
                    return await self._create_entry(self._meter_points[0])

            except AbortFlow:
                # Let abort flow propagate (e.g., already_configured)
                raise
            except WienerNetzeAuthError:
                _LOGGER.error("Authentication failed")
                errors["base"] = "invalid_auth"
            except WienerNetzeConnectionError:
                _LOGGER.error("Connection failed")
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_meter_point(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle meter point selection."""
        if user_input is not None:
            # Find selected meter point
            selected_id = user_input["meter_point"]
            meter_point = next(
                (
                    mp
                    for mp in self._meter_points
                    if mp["zaehlpunktnummer"] == selected_id
                ),
                None,
            )

            if meter_point:
                return await self._create_entry(meter_point)

        # Build selector options
        options = [
            {
                "value": mp["zaehlpunktnummer"],
                "label": (
                    f"{format_meter_point_address(mp)} "
                    f"({mp['zaehlpunktnummer'][-8:]})"
                ),
            }
            for mp in self._meter_points
        ]

        data_schema = vol.Schema(
            {
                vol.Required("meter_point"): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="meter_point",
            data_schema=data_schema,
        )

    async def _create_entry(self, meter_point: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        # Create unique ID from meter point
        unique_id = meter_point["zaehlpunktnummer"]

        # Check if already configured
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # Create title
        title = format_meter_point_address(meter_point)

        # Create entry
        return self.async_create_entry(
            title=title,
            data={
                **self._credentials,
                "meter_points": [meter_point],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return WienerNetzeOptionsFlow(config_entry)


class WienerNetzeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Wiener Netze Smart Meter."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # For now, no options to configure
        # Future: update interval, granularity, etc.
        return self.async_show_form(step_id="init")
