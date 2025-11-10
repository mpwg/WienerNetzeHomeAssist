# Task 14: Device Registry Integration

**Category:** Home Assistant Integration Core
**Priority:** Medium
**Estimated Effort:** 2-3 hours
**Status:** Not Started

## Description

Implement proper device registry integration to group all entities from the same smart meter under a single device in Home Assistant.

## Prerequisites

- **Task 12** completed (Data Update Coordinator)
- Understanding of Home Assistant device registry

## Objectives

1. Create device information for each meter point
2. Link entities to devices
3. Add device attributes (manufacturer, model, firmware, etc.)
4. Implement device diagnostics
5. Test device information in UI

## Deliverables

- [ ] Device info helper functions
- [ ] Device attributes populated from API data
- [ ] Entities linked to devices
- [ ] Device diagnostics data
- [ ] Device appears correctly in UI

## Implementation

### 1. Add Device Helper Functions to api.py

```python
"""Add device helper functions."""

def get_device_info_from_meter_point(meter_point: dict) -> dict[str, Any]:
    """Extract device information from meter point data.

    Args:
        meter_point: Meter point data from API

    Returns:
        Dictionary with device information

    """
    anlage = meter_point.get("anlage", {})
    geraet = meter_point.get("geraet", {})

    return {
        "identifiers": meter_point.get("zaehlpunktnummer"),
        "manufacturer": "Wiener Netze",
        "model": geraet.get("geraetetyp", "Smart Meter"),
        "name": format_meter_point_address(meter_point),
        "sw_version": geraet.get("firmware", "Unknown"),
        "serial_number": geraet.get("geraetnummer"),
        "configuration_url": "https://smartmeter-web.wienernetze.at",
        "suggested_area": "Utility",
    }


def format_meter_point_address(meter_point: dict) -> str:
    """Format meter point address for display.

    Args:
        meter_point: Meter point data from API

    Returns:
        Formatted address string

    """
    verbrauchsstelle = meter_point.get("verbrauchsstelle", {})
    adresse = verbrauchsstelle.get("adresse", {})

    strasse = adresse.get("strasse", "")
    hausnummer = adresse.get("hausnummer", "")
    tuernummer = adresse.get("tuernummer", "")
    stiege = adresse.get("stiege", "")
    plz = adresse.get("postleitzahl", "")
    ort = adresse.get("ort", "")

    # Build address string
    parts = []

    # Street and number
    if strasse:
        street_part = strasse
        if hausnummer:
            street_part += f" {hausnummer}"
        if stiege:
            street_part += f"/{stiege}"
        if tuernummer:
            street_part += f"/{tuernummer}"
        parts.append(street_part)

    # City
    if plz or ort:
        city_part = f"{plz} {ort}".strip()
        parts.append(city_part)

    if parts:
        return ", ".join(parts)

    # Fallback to meter point number
    meter_id = meter_point.get("zaehlpunktnummer", "")
    return f"Smart Meter {meter_id[-8:]}" if meter_id else "Smart Meter"
```

### 2. Update Coordinator to Store Device Info

```python
"""Update coordinator.py to include device info."""

async def _async_update_data(self) -> dict[str, Any]:
    """Fetch data from API."""
    _LOGGER.debug("Fetching Wiener Netze Smart Meter data")

    try:
        data = {}

        for meter_point in self.meter_points:
            meter_id = meter_point["zaehlpunktnummer"]

            # Get device info from meter point
            from .api import get_device_info_from_meter_point
            device_info = get_device_info_from_meter_point(meter_point)

            # Get consumption data
            today = date.today()
            date_from = today.isoformat()
            date_to = today.isoformat()

            consumption_data = await self.api_client.get_consumption_data(
                meter_point=meter_id,
                date_from=date_from,
                date_to=date_to,
                granularity=GRANULARITY_QUARTER_HOUR,
            )

            # Store data for this meter point
            data[meter_id] = {
                "meter_point": meter_point,
                "device_info": device_info,
                "consumption": consumption_data,
                "last_update": self.hass.loop.time(),
            }

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
```

### 3. Update Sensor Entity Device Info

Update the base sensor entity in `sensor.py`:

```python
"""Update sensor entity with better device info."""

class WienerNetzeSensorEntity(CoordinatorEntity, SensorEntity):
    """Base sensor entity for Wiener Netze."""

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._meter_id = meter_id
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        meter_data = self.coordinator.get_meter_data(self._meter_id)

        if not meter_data:
            # Fallback device info
            return DeviceInfo(
                identifiers={(DOMAIN, self._meter_id)},
                name=f"Smart Meter {self._meter_id[-8:]}",
                manufacturer="Wiener Netze",
                model="Smart Meter",
            )

        device_info = meter_data.get("device_info", {})

        return DeviceInfo(
            identifiers={(DOMAIN, self._meter_id)},
            name=device_info.get("name", f"Smart Meter {self._meter_id[-8:]}"),
            manufacturer=device_info.get("manufacturer", "Wiener Netze"),
            model=device_info.get("model", "Smart Meter"),
            sw_version=device_info.get("sw_version"),
            serial_number=device_info.get("serial_number"),
            configuration_url=device_info.get("configuration_url"),
            suggested_area=device_info.get("suggested_area"),
        )
```

### 4. Add Device Diagnostics

Create `diagnostics.py`:

```python
"""Diagnostics support for Wiener Netze Smart Meter."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import WienerNetzeDataCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        Diagnostic data

    """
    coordinator: WienerNetzeDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None,
            "update_interval": coordinator.update_interval.total_seconds(),
            "meter_count": len(coordinator.meter_points),
        },
        "meters": {},
    }

    # Add data for each meter (redact sensitive info)
    if coordinator.data:
        for meter_id, meter_data in coordinator.data.items():
            meter_point = meter_data.get("meter_point", {})
            device_info = meter_data.get("device_info", {})
            consumption = meter_data.get("consumption", {})

            diagnostics_data["meters"][meter_id] = {
                "device_info": {
                    "manufacturer": device_info.get("manufacturer"),
                    "model": device_info.get("model"),
                    "sw_version": device_info.get("sw_version"),
                    "serial_number": device_info.get("serial_number"),
                },
                "consumption_data": {
                    "reading_count": len(consumption.get("messwerte", [])),
                    "obis_code": consumption.get("obisCode"),
                    "unit": consumption.get("einheit"),
                    "latest_reading": consumption.get("messwerte", [{}])[-1]
                    if consumption.get("messwerte")
                    else None,
                },
                "last_update": meter_data.get("last_update"),
            }

    return diagnostics_data
```

### 5. Update manifest.json

Ensure diagnostics is listed:

```json
{
  "domain": "wiener_netze",
  "name": "Wiener Netze Smart Meter",
  "codeowners": ["@mpwg"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/mpwg/WienerNetzeHomeAssist",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/mpwg/WienerNetzeHomeAssist/issues",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0",
  "diagnostics": ["config_entry"]
}
```

### 6. Create Unit Tests

Add to `tests/test_device_registry.py`:

```python
"""Tests for device registry integration."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.wiener_netze.const import DOMAIN
from tests.utils import load_json_fixture


async def test_device_registry_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
):
    """Test device registry entry is created."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_coordinator.meter_points = meter_points
    mock_coordinator.data = {
        meter_points[0]["zaehlpunktnummer"]: {
            "meter_point": meter_points[0],
            "consumption": consumption_data,
            "device_info": {
                "manufacturer": "Wiener Netze",
                "model": "Smart Meter",
                "sw_version": "1.0",
            },
        }
    }

    # Setup integration
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

    # Get device registry
    device_registry = dr.async_get(hass)

    # Setup sensors (which creates devices)
    from custom_components.wiener_netze.sensor import async_setup_entry

    entities = []

    def add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, add_entities)

    # Verify device was created
    meter_id = meter_points[0]["zaehlpunktnummer"]
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, meter_id)}
    )

    assert device is not None
    assert device.manufacturer == "Wiener Netze"
    assert device.model == "Smart Meter"


async def test_device_diagnostics(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
):
    """Test device diagnostics."""
    from custom_components.wiener_netze.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_coordinator.meter_points = meter_points
    mock_coordinator.data = {
        meter_points[0]["zaehlpunktnummer"]: {
            "meter_point": meter_points[0],
            "consumption": consumption_data,
            "device_info": {
                "manufacturer": "Wiener Netze",
                "model": "Smart Meter",
            },
        }
    }

    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

    diagnostics = await async_get_config_entry_diagnostics(
        hass, mock_config_entry
    )

    assert diagnostics
    assert "entry" in diagnostics
    assert "coordinator" in diagnostics
    assert "meters" in diagnostics
    assert diagnostics["coordinator"]["meter_count"] == len(meter_points)
```

## Acceptance Criteria

- [ ] Device info extracted from meter point data
- [ ] Devices created in device registry
- [ ] All entities linked to correct device
- [ ] Device attributes populated (manufacturer, model, etc.)
- [ ] Device diagnostics implemented
- [ ] Address formatting works correctly
- [ ] Devices appear in Home Assistant UI
- [ ] Device page shows all entities
- [ ] Diagnostics downloadable from device page
- [ ] All tests passing

## Testing

```bash
# Run device registry tests
pytest tests/test_device_registry.py -v

# Test in Home Assistant
# 1. Add integration
# 2. Go to Settings → Devices & Services
# 3. Click on Wiener Netze integration
# 4. Verify device appears with correct info
# 5. Click device to see all entities
# 6. Click three dots → Download diagnostics
# 7. Verify diagnostics file contains expected data
```

## References

- [Device Registry Documentation](https://developers.home-assistant.io/docs/device_registry_index/)
- [Device Info](https://developers.home-assistant.io/docs/device_registry_index/#device-info)
- [Diagnostics](https://developers.home-assistant.io/docs/integration_setup_failures/#diagnostics)

## Notes

- Use meter point number as device identifier
- Format address nicely for device name
- Include serial number from API if available
- Link to Wiener Netze web portal in configuration_url
- Suggest "Utility" as default area
- Redact sensitive data in diagnostics
- Include firmware version if available from API
- Test with meters that have partial address data

## Next Task

→ **Task 15:** Sensor Platform Implementation
