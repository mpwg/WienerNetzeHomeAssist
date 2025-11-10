# Task 15: Sensor Platform Implementation

**Category:** Entity Platform Implementation
**Priority:** Critical
**Estimated Effort:** 4-5 hours
**Status:** Not Started

## Description

Implement sensor entities that display energy consumption data from the Wiener Netze Smart Meter in Home Assistant.

## Prerequisites

- **Task 12** completed (Data Update Coordinator)
- Understanding of Home Assistant sensor platform

## Objectives

1. Create base sensor entity class
2. Implement current power sensor (15-minute readings)
3. Implement daily energy sensor
4. Add device registry integration
5. Add proper state classes and device classes
6. Create unit tests

## Deliverables

- [ ] Base `WienerNetzeSensorEntity` class
- [ ] Current power sensor
- [ ] Daily energy sensor
- [ ] Device information
- [ ] Unit tests for sensors

## Implementation

### 1. Implement sensor.py

```python
"""Sensor platform for Wiener Netze Smart Meter."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import format_meter_point_address
from .const import DOMAIN
from .coordinator import WienerNetzeDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wiener Netze sensors from config entry.

    Args:
        hass: Home Assistant instance
        config_entry: Config entry
        async_add_entities: Callback to add entities

    """
    coordinator: WienerNetzeDataCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    sensors: list[SensorEntity] = []

    # Create sensors for each meter point
    for meter_point in coordinator.meter_points:
        meter_id = meter_point["zaehlpunktnummer"]

        sensors.extend(
            [
                WienerNetzeCurrentPowerSensor(coordinator, meter_id),
                WienerNetzeDailyEnergySensor(coordinator, meter_id),
            ]
        )

    _LOGGER.debug("Adding %d sensors", len(sensors))
    async_add_entities(sensors)


class WienerNetzeSensorEntity(CoordinatorEntity, SensorEntity):
    """Base sensor entity for Wiener Netze."""

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor.

        Args:
            coordinator: Data coordinator
            meter_id: Meter point number

        """
        super().__init__(coordinator)
        self._meter_id = meter_id
        self._meter_point = next(
            mp
            for mp in coordinator.meter_points
            if mp["zaehlpunktnummer"] == meter_id
        )

        # Entity attributes
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._meter_id)},
            name=f"Smart Meter {self._meter_id[-8:]}",
            manufacturer="Wiener Netze",
            model="Smart Meter",
            sw_version="1.0",
            configuration_url="https://www.wienerstadtwerke.at",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._meter_id in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attributes = {
            "meter_point": self._meter_id,
            "address": format_meter_point_address(self._meter_point),
        }

        meter_data = self.coordinator.get_meter_data(self._meter_id)
        if meter_data:
            attributes["last_update"] = datetime.fromtimestamp(
                meter_data.get("last_update", 0)
            ).isoformat()

        return attributes


class WienerNetzeCurrentPowerSensor(WienerNetzeSensorEntity):
    """Sensor for current power consumption."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, meter_id)

        self._attr_unique_id = f"{meter_id}_current_power"
        self._attr_translation_key = "current_power"

    @property
    def native_value(self) -> float | None:
        """Return current power in watts."""
        latest_reading = self.coordinator.get_latest_reading(self._meter_id)

        if not latest_reading:
            return None

        # Convert kWh to W (15-minute interval)
        # kWh * 1000 * 4 (quarters per hour) = W
        kwh = latest_reading.get("wert", 0.0)
        watts = kwh * 1000 * 4

        return round(watts, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes

        latest_reading = self.coordinator.get_latest_reading(self._meter_id)
        if latest_reading:
            attributes.update(
                {
                    "reading_time_from": latest_reading.get("zeitpunktVon"),
                    "reading_time_to": latest_reading.get("zeitpunktBis"),
                    "quality": latest_reading.get("qualitaet"),
                    "reading_kwh": latest_reading.get("wert"),
                }
            )

        return attributes


class WienerNetzeDailyEnergySensor(WienerNetzeSensorEntity):
    """Sensor for daily energy consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, meter_id)

        self._attr_unique_id = f"{meter_id}_daily_energy"
        self._attr_translation_key = "daily_energy"

    @property
    def native_value(self) -> float | None:
        """Return daily energy consumption in kWh."""
        total = self.coordinator.get_total_consumption_today(self._meter_id)

        if total == 0:
            return None

        return round(total, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attributes = super().extra_state_attributes

        meter_data = self.coordinator.get_meter_data(self._meter_id)
        if meter_data:
            readings = meter_data.get("consumption", {}).get("messwerte", [])
            attributes.update(
                {
                    "reading_count": len(readings),
                    "validated_readings": len(
                        [r for r in readings if r.get("qualitaet") == "VAL"]
                    ),
                    "estimated_readings": len(
                        [r for r in readings if r.get("qualitaet") == "EST"]
                    ),
                }
            )

        return attributes
```

### 2. Update translations/en.json

```json
{
  "entity": {
    "sensor": {
      "current_power": {
        "name": "Current power"
      },
      "daily_energy": {
        "name": "Daily energy"
      }
    }
  }
}
```

### 3. Update translations/de.json

```json
{
  "entity": {
    "sensor": {
      "current_power": {
        "name": "Aktuelle Leistung"
      },
      "daily_energy": {
        "name": "Tagesverbrauch"
      }
    }
  }
}
```

### 4. Create Unit Tests

Add to `tests/test_sensor.py`:

```python
"""Tests for sensor.py."""
import pytest
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from unittest.mock import AsyncMock

from custom_components.wiener_netze.const import DOMAIN
from custom_components.wiener_netze.sensor import (
    WienerNetzeCurrentPowerSensor,
    WienerNetzeDailyEnergySensor,
    async_setup_entry,
)
from tests.utils import load_json_fixture


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
):
    """Test sensor platform setup."""
    # Setup coordinator with data
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    mock_coordinator.meter_points = meter_points

    # Store coordinator
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}

    # Setup sensors
    entities = []

    def add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, add_entities)

    # Should create 2 sensors per meter point
    assert len(entities) == len(meter_points) * 2


async def test_current_power_sensor(
    hass: HomeAssistant,
    mock_coordinator,
):
    """Test current power sensor."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_coordinator.meter_points = meter_points
    mock_coordinator.data = {
        meter_points[0]["zaehlpunktnummer"]: {
            "meter_point": meter_points[0],
            "consumption": consumption_data,
            "last_update": 1234567890,
        }
    }

    meter_id = meter_points[0]["zaehlpunktnummer"]
    sensor = WienerNetzeCurrentPowerSensor(mock_coordinator, meter_id)

    assert sensor.unique_id == f"{meter_id}_current_power"
    assert sensor.device_class == "power"
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT

    # Latest reading: 0.18 kWh over 15 minutes
    # = 0.18 * 1000 * 4 = 720 W
    assert sensor.native_value == 720.0


async def test_daily_energy_sensor(
    hass: HomeAssistant,
    mock_coordinator,
):
    """Test daily energy sensor."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    mock_coordinator.meter_points = meter_points
    mock_coordinator.data = {
        meter_points[0]["zaehlpunktnummer"]: {
            "meter_point": meter_points[0],
            "consumption": consumption_data,
            "last_update": 1234567890,
        }
    }

    meter_id = meter_points[0]["zaehlpunktnummer"]
    sensor = WienerNetzeDailyEnergySensor(mock_coordinator, meter_id)

    assert sensor.unique_id == f"{meter_id}_daily_energy"
    assert sensor.device_class == "energy"
    assert sensor.native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR

    # Total: 0.15 + 0.12 + 0.18 = 0.45 kWh
    assert sensor.native_value == 0.45


async def test_sensor_availability(
    hass: HomeAssistant,
    mock_coordinator,
):
    """Test sensor availability."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]

    mock_coordinator.meter_points = meter_points
    mock_coordinator.last_update_success = True
    mock_coordinator.data = {
        meter_points[0]["zaehlpunktnummer"]: {
            "meter_point": meter_points[0],
            "consumption": {},
        }
    }

    meter_id = meter_points[0]["zaehlpunktnummer"]
    sensor = WienerNetzeCurrentPowerSensor(mock_coordinator, meter_id)

    # Should be available
    assert sensor.available is True

    # No data - should be unavailable
    mock_coordinator.data = {}
    assert sensor.available is False


async def test_sensor_device_info(
    hass: HomeAssistant,
    mock_coordinator,
):
    """Test sensor device information."""
    meter_points = load_json_fixture("meter_points.json")["zaehlpunkte"]
    mock_coordinator.meter_points = meter_points

    meter_id = meter_points[0]["zaehlpunktnummer"]
    sensor = WienerNetzeCurrentPowerSensor(mock_coordinator, meter_id)

    device_info = sensor.device_info

    assert device_info["identifiers"] == {(DOMAIN, meter_id)}
    assert "Smart Meter" in device_info["name"]
    assert device_info["manufacturer"] == "Wiener Netze"
```

## Acceptance Criteria

- [ ] Sensor platform implemented
- [ ] Current power sensor shows watts
- [ ] Daily energy sensor shows kWh
- [ ] Sensors linked to devices
- [ ] Proper device class and state class
- [ ] Extra attributes with reading details
- [ ] Sensors show as unavailable when no data
- [ ] All tests passing
- [ ] Sensors appear in Home Assistant UI

## Testing

```bash
# Run sensor tests
pytest tests/test_sensor.py -v

# Check coverage
pytest tests/test_sensor.py --cov=custom_components.wiener_netze.sensor --cov-report=term-missing

# Test in Home Assistant
# 1. Add integration
# 2. Check Developer Tools → States
# 3. Verify sensors appear with correct values
```

## References

- [Sensor Platform Documentation](https://developers.home-assistant.io/docs/core/entity/sensor/)
- [Device Classes](https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes)
- [State Classes](https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes)

## Notes

- Current power: Convert 15-minute kWh to instantaneous W
- Daily energy: Sum all readings for today
- Use `TOTAL_INCREASING` for cumulative energy
- Use `MEASUREMENT` for instantaneous power
- Include quality indicator in attributes
- Show last 8 digits of meter ID in device name
- Use translation keys for entity names

## Next Task

→ **Task 19-21:** Translations (complete strings.json and translations)
