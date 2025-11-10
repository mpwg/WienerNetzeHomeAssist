# Task 12: Data Update Coordinator

**Category:** Home Assistant Integration Core
**Priority:** Critical
**Estimated Effort:** 3-4 hours
**Status:** Not Started

## Description

Implement the DataUpdateCoordinator to manage periodic data fetching from the Wiener Netze API and provide data to sensor entities.

## Prerequisites

- **Task 07** completed (API Client - Consumption Data Retrieval)
- Understanding of Home Assistant DataUpdateCoordinator pattern

## Objectives

1. Create coordinator subclass
2. Implement data fetching from API
3. Handle errors and retries
4. Manage update interval
5. Store consumption data for sensors
6. Add unit tests

## Deliverables

- [ ] `WienerNetzeDataCoordinator` class
- [ ] Data fetching method
- [ ] Error handling
- [ ] Data transformation
- [ ] Unit tests for coordinator

## Implementation

### 1. Implement coordinator.py

```python
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
    CONF_METER_POINTS,
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
        self.meter_points = config_entry.data.get(CONF_METER_POINTS, [])

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

                _LOGGER.debug(
                    "Fetching consumption data for %s", meter_id
                )

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
```

### 2. Update Constants

Add to `const.py`:

```python
# Update Interval
DEFAULT_SCAN_INTERVAL = 15  # minutes

# Data keys
CONF_METER_POINTS = "meter_points"
```

### 3. Create Unit Tests

Add to `tests/test_coordinator.py`:

```python
"""Tests for coordinator.py."""
import pytest
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.wiener_netze.coordinator import (
    WienerNetzeDataCoordinator,
)
from custom_components.wiener_netze.api import (
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
    WienerNetzeApiError,
)
from tests.utils import load_json_fixture


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test successful coordinator update."""
    # Setup mock data
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_config_entry.data["meter_points"] = meter_points
    mock_api_client.get_consumption_data = AsyncMock(
        return_value=consumption_data
    )

    # Create coordinator
    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    # Update data
    await coordinator.async_refresh()

    # Verify data
    assert coordinator.data
    meter_id = meter_points[0]["zaehlpunktnummer"]
    assert meter_id in coordinator.data
    assert coordinator.data[meter_id]["consumption"] == consumption_data


async def test_coordinator_update_auth_error(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test coordinator update with auth error."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    mock_config_entry.data["meter_points"] = meter_points

    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=WienerNetzeAuthError("Invalid credentials")
    )

    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    # Should raise ConfigEntryAuthFailed
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.async_refresh()


async def test_coordinator_update_connection_error(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test coordinator update with connection error."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    mock_config_entry.data["meter_points"] = meter_points

    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=WienerNetzeConnectionError("Connection failed")
    )

    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    # Should raise UpdateFailed
    with pytest.raises(UpdateFailed):
        await coordinator.async_refresh()


async def test_get_meter_data(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting meter data."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_config_entry.data["meter_points"] = meter_points
    mock_api_client.get_consumption_data = AsyncMock(
        return_value=consumption_data
    )

    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    meter_data = coordinator.get_meter_data(meter_id)

    assert meter_data
    assert meter_data["meter_point"] == meter_points[0]
    assert meter_data["consumption"] == consumption_data


async def test_get_latest_reading(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting latest reading."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_config_entry.data["meter_points"] = meter_points
    mock_api_client.get_consumption_data = AsyncMock(
        return_value=consumption_data
    )

    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    latest = coordinator.get_latest_reading(meter_id)

    assert latest
    assert latest == consumption_data["messwerte"][-1]


async def test_get_total_consumption_today(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting total consumption."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_config_entry.data["meter_points"] = meter_points
    mock_api_client.get_consumption_data = AsyncMock(
        return_value=consumption_data
    )

    coordinator = WienerNetzeDataCoordinator(
        hass, mock_api_client, mock_config_entry
    )

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    total = coordinator.get_total_consumption_today(meter_id)

    # Sum of values from fixture: 0.15 + 0.12 + 0.18 = 0.45
    assert total == 0.45
```

## Acceptance Criteria

- [ ] Coordinator fetches data from API
- [ ] Updates every 15 minutes (configurable)
- [ ] Handles authentication errors
- [ ] Handles connection errors
- [ ] Stores data for all meter points
- [ ] Provides helper methods for sensor access
- [ ] All tests passing
- [ ] Code coverage >80%

## Testing

```bash
# Run coordinator tests
pytest tests/test_coordinator.py -v

# Check coverage
pytest tests/test_coordinator.py --cov=custom_components.wiener_netze.coordinator --cov-report=term-missing
```

## References

- [DataUpdateCoordinator Documentation](https://developers.home-assistant.io/docs/integration_fetching_data/)
- [Update Coordinator Best Practices](https://developers.home-assistant.io/docs/integration_fetching_data/#coordinated-single-api-poll-for-data-for-all-entities)

## Notes

- Use `DEFAULT_SCAN_INTERVAL` for update frequency
- Raise `ConfigEntryAuthFailed` for auth errors (triggers reauth)
- Raise `UpdateFailed` for temporary errors (will retry)
- Store meter_id as key for easy sensor access
- Fetch today's data on each update
- Consider caching yesterday's data for daily totals

## Next Task

→ **Task 15:** Sensor Platform Implementation
