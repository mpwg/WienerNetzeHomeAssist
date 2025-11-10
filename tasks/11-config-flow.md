# Task 11: Config Flow Implementation

**Category:** Home Assistant Integration Core
**Priority:** Critical
**Estimated Effort:** 4-5 hours
**Status:** Not Started

## Description

Implement the configuration flow that allows users to set up the integration through the Home Assistant UI.

## Prerequisites

- **Task 07** completed (API Client - Consumption Data Retrieval)
- Understanding of Home Assistant config flow patterns

## Objectives

1. Implement user input step for credentials
2. Validate credentials with API
3. Implement meter point selection step
4. Handle errors gracefully with user-friendly messages
5. Support reconfiguration (options flow)

## Deliverables

- [ ] Config flow with user input
- [ ] Credential validation
- [ ] Meter point selection
- [ ] Error handling and user feedback
- [ ] Options flow for changes
- [ ] Unit tests for config flow

## Implementation

### 1. Implement config_flow.py

```python
"""Config flow for Wiener Netze Smart Meter integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import (
    WienerNetzeApiClient,
    WienerNetzeApiError,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
)
from .const import (
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_METER_POINTS,
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
                    return self._create_entry(self._meter_points[0])

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
                (mp for mp in self._meter_points if mp["zaehlpunktnummer"] == selected_id),
                None,
            )

            if meter_point:
                return self._create_entry(meter_point)

        # Build selector options
        from .api import format_meter_point_address

        options = [
            {
                "value": mp["zaehlpunktnummer"],
                "label": f"{format_meter_point_address(mp)} ({mp['zaehlpunktnummer'][-8:]})",
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

    def _create_entry(self, meter_point: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        from .api import format_meter_point_address

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
                CONF_METER_POINTS: [meter_point],
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
```

### 2. Update strings.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter Setup",
        "description": "Enter your API credentials from the WSTW API Portal",
        "data": {
          "client_id": "OAuth2 Client ID",
          "client_secret": "OAuth2 Client Secret",
          "api_key": "API Gateway Key"
        }
      },
      "meter_point": {
        "title": "Select Meter Point",
        "description": "Select the smart meter (Zählpunkt) to monitor",
        "data": {
          "meter_point": "Meter Point"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid credentials. Please check your Client ID, Client Secret, and API Key.",
      "cannot_connect": "Cannot connect to Wiener Netze API. Please check your internet connection.",
      "no_meter_points": "No smart meters found for this account.",
      "unknown": "Unexpected error occurred. Please try again."
    },
    "abort": {
      "already_configured": "This meter point is already configured."
    }
  }
}
```

### 3. Update translations/en.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter Setup",
        "description": "Enter your API credentials from the WSTW API Portal",
        "data": {
          "client_id": "OAuth2 Client ID",
          "client_secret": "OAuth2 Client Secret",
          "api_key": "API Gateway Key"
        }
      },
      "meter_point": {
        "title": "Select Meter Point",
        "description": "Select the smart meter (Zählpunkt) to monitor",
        "data": {
          "meter_point": "Meter Point"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid credentials. Please check your Client ID, Client Secret, and API Key.",
      "cannot_connect": "Cannot connect to Wiener Netze API. Please check your internet connection.",
      "no_meter_points": "No smart meters found for this account.",
      "unknown": "Unexpected error occurred. Please try again."
    },
    "abort": {
      "already_configured": "This meter point is already configured."
    }
  }
}
```

### 4. Create Unit Tests

Add to `tests/test_config_flow.py`:

```python
"""Tests for config_flow.py."""
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.wiener_netze.const import (
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)
from tests.utils import load_json_fixture


async def test_form_user_step(hass: HomeAssistant):
    """Test user step form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_success_single_meter(hass: HomeAssistant):
    """Test successful setup with single meter point."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client.get_meter_points = AsyncMock(
            return_value=load_json_fixture("meter_points.json")["zaehlpunkte"][:1]
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"]
        assert result["data"][CONF_CLIENT_ID] == "test_client"


async def test_form_user_invalid_auth(hass: HomeAssistant):
    """Test invalid authentication."""
    from custom_components.wiener_netze.api import WienerNetzeAuthError

    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeAuthError("Invalid credentials")
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "bad_client",
                CONF_CLIENT_SECRET: "bad_secret",
                CONF_API_KEY: "bad_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_form_user_cannot_connect(hass: HomeAssistant):
    """Test connection error."""
    from custom_components.wiener_netze.api import WienerNetzeConnectionError

    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeConnectionError("Connection failed")
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_multiple_meters(hass: HomeAssistant):
    """Test setup with multiple meter points."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client.get_meter_points = AsyncMock(
            return_value=load_json_fixture("meter_points.json")["zaehlpunkte"]
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        # Should show meter point selection
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "meter_point"
```

## Acceptance Criteria

- [ ] Config flow accepts user credentials
- [ ] Credentials validated with API
- [ ] Meter points fetched and displayed
- [ ] Single meter point creates entry automatically
- [ ] Multiple meter points show selection UI
- [ ] Errors displayed with user-friendly messages
- [ ] Duplicate meter points prevented (unique_id)
- [ ] All tests passing
- [ ] Integration appears in Home Assistant UI

## Testing

```bash
# Run config flow tests
pytest tests/test_config_flow.py -v

# Test in Home Assistant
# 1. Go to Settings → Devices & Services
# 2. Click "+ Add Integration"
# 3. Search for "Wiener Netze"
# 4. Follow setup wizard
```

## References

- [Config Flow Documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Config Flow Best Practices](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#best-practices)

## Notes

- Use `async_set_unique_id()` with meter point number
- Call `_abort_if_unique_id_configured()` to prevent duplicates
- Store all credentials and meter point in config entry data
- Use SelectSelector for meter point dropdown
- Show last 8 digits of meter point number in UI for brevity

## Next Task

→ **Task 12:** Data Update Coordinator
