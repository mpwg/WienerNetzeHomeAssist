"""DataUpdateCoordinator for Wiener Netze Smart Meter."""
from datetime import date, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    WienerNetzeApiClient,
    WienerNetzeApiError,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
)
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    GRANULARITY_QUARTER_HOUR,
)

_LOGGER = logging.getLogger(__name__)


class WienerNetzeDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Wiener Netze data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: WienerNetzeApiClient,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator.

        Args:
            hass: Home Assistant instance
            api_client: API client instance
            config_entry: Config entry

        """
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.api_client = api_client
        self.config_entry = config_entry
        self.meter_points = config_entry.data.get("meter_points", [])

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API.

        Returns:
            Dictionary of meter point data

        Raises:
            ConfigEntryAuthFailed: Authentication failed
            UpdateFailed: Update failed

        """
        _LOGGER.debug("Fetching Wiener Netze Smart Meter data")

        try:
            data = {}

            for meter_point in self.meter_points:
                meter_id = meter_point["zaehlpunktnummer"]

                # Get today's data
                today = date.today()
                date_from = today.isoformat()
                date_to = today.isoformat()

                _LOGGER.debug("Fetching consumption data for %s", meter_id)

                consumption_data = await self.api_client.get_consumption_data(
                    meter_point=meter_id,
                    date_from=date_from,
                    date_to=date_to,
                    granularity=GRANULARITY_QUARTER_HOUR,
                )

                # Store data for this meter point
                data[meter_id] = {
                    "meter_point": meter_point,
                    "consumption": consumption_data,
                    "last_update": self.hass.loop.time(),
                }

                _LOGGER.debug(
                    "Retrieved %d readings for %s",
                    len(consumption_data.get("messwerte", [])),
                    meter_id,
                )

            _LOGGER.info(
                "Successfully updated data for %d meter point(s)",
                len(data),
            )

            return data

        except WienerNetzeAuthError as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise ConfigEntryAuthFailed from err
        except WienerNetzeConnectionError as err:
            _LOGGER.warning("Connection failed: %s", err)
            raise UpdateFailed(f"Connection error: {err}") from err
        except WienerNetzeApiError as err:
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def get_meter_data(self, meter_id: str) -> dict[str, Any] | None:
        """Get data for specific meter point.

        Args:
            meter_id: Meter point number

        Returns:
            Meter data or None if not found

        """
        if not self.data:
            return None

        return self.data.get(meter_id)

    def get_latest_reading(self, meter_id: str) -> dict[str, Any] | None:
        """Get latest reading for meter point.

        Args:
            meter_id: Meter point number

        Returns:
            Latest reading or None

        """
        meter_data = self.get_meter_data(meter_id)
        if not meter_data:
            return None

        readings = meter_data.get("consumption", {}).get("messwerte", [])
        if not readings:
            return None

        # Return most recent reading
        return readings[-1]

    def get_total_consumption_today(self, meter_id: str) -> float:
        """Get total consumption for today.

        Args:
            meter_id: Meter point number

        Returns:
            Total consumption in kWh

        """
        meter_data = self.get_meter_data(meter_id)
        if not meter_data:
            return 0.0

        readings = meter_data.get("consumption", {}).get("messwerte", [])
        return sum(reading.get("wert", 0.0) for reading in readings)
