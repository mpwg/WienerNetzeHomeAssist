# Task 16: Additional Consumption Sensors

**Category:** Entity Platform Implementation
**Priority:** Medium
**Estimated Effort:** 2-3 hours
**Status:** Not Started

## Description

Implement additional consumption sensors for monthly, yearly, and meter reading data to provide comprehensive energy monitoring.

## Prerequisites

- **Task 15** completed (Sensor Platform Implementation)
- Understanding of Home Assistant sensor state classes

## Objectives

1. Create monthly energy sensor
2. Create yearly energy sensor
3. Create meter reading sensor
4. Add historical data sensors
5. Implement proper state classes
6. Create unit tests

## Deliverables

- [ ] Monthly energy consumption sensor
- [ ] Yearly energy consumption sensor
- [ ] Cumulative meter reading sensor
- [ ] Unit tests for all new sensors

## Implementation

### 1. Monthly Energy Sensor

Add to `sensor.py`:

```python
class WienerNetzeMonthlyEnergySensor(WienerNetzeSensorEntity):
    """Sensor for monthly energy consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, meter_id)
        self._attr_unique_id = f"{meter_id}_monthly_energy"
        self._attr_translation_key = "monthly_energy"

    @property
    def native_value(self) -> float | None:
        """Return monthly energy consumption in kWh."""
        total = self.coordinator.get_total_consumption_month(self._meter_id)
        if total == 0:
            return None
        return round(total, 3)
```

### 2. Yearly Energy Sensor

```python
class WienerNetzeYearlyEnergySensor(WienerNetzeSensorEntity):
    """Sensor for yearly energy consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(
        self,
        coordinator: WienerNetzeDataCoordinator,
        meter_id: str,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, meter_id)
        self._attr_unique_id = f"{meter_id}_yearly_energy"
        self._attr_translation_key = "yearly_energy"

    @property
    def native_value(self) -> float | None:
        """Return yearly energy consumption in kWh."""
        total = self.coordinator.get_total_consumption_year(self._meter_id)
        if total == 0:
            return None
        return round(total, 3)
```

### 3. Meter Reading Sensor

```python
class WienerNetzeMeterReadingSensor(WienerNetzeSensorEntity):
    """Sensor for cumulative meter reading."""

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
        self._attr_unique_id = f"{meter_id}_meter_reading"
        self._attr_translation_key = "meter_reading"

    @property
    def native_value(self) -> float | None:
        """Return cumulative meter reading in kWh."""
        reading = self.coordinator.get_meter_reading(self._meter_id)
        if reading is None:
            return None
        return round(reading, 3)
```

### 4. Update Coordinator with Additional Methods

Add to `coordinator.py`:

```python
def get_total_consumption_month(self, meter_id: str) -> float:
    """Get total consumption for current month.

    Args:
        meter_id: Meter point number

    Returns:
        Total consumption in kWh

    """
    meter_data = self.get_meter_data(meter_id)
    if not meter_data:
        return 0.0

    readings = meter_data.get("consumption", {}).get("messwerte", [])

    # Filter for current month
    now = date.today()
    month_start = now.replace(day=1)

    total = 0.0
    for reading in readings:
        reading_date = reading.get("zeitpunktVon", "")
        if reading_date >= month_start.isoformat():
            total += reading.get("wert", 0.0)

    return total


def get_total_consumption_year(self, meter_id: str) -> float:
    """Get total consumption for current year.

    Args:
        meter_id: Meter point number

    Returns:
        Total consumption in kWh

    """
    meter_data = self.get_meter_data(meter_id)
    if not meter_data:
        return 0.0

    readings = meter_data.get("consumption", {}).get("messwerte", [])

    # Filter for current year
    now = date.today()
    year_start = now.replace(month=1, day=1)

    total = 0.0
    for reading in readings:
        reading_date = reading.get("zeitpunktVon", "")
        if reading_date >= year_start.isoformat():
            total += reading.get("wert", 0.0)

    return total


def get_meter_reading(self, meter_id: str) -> float | None:
    """Get cumulative meter reading.

    Args:
        meter_id: Meter point number

    Returns:
        Meter reading in kWh or None

    """
    meter_data = self.get_meter_data(meter_id)
    if not meter_data:
        return None

    # Get meter reading from API (METER_READ value type)
    meter_reading_data = meter_data.get("meter_reading")
    if meter_reading_data:
        readings = meter_reading_data.get("messwerte", [])
        if readings:
            # Return most recent meter reading
            return readings[-1].get("wert")

    return None
```

### 5. Update Sensor Setup

Update `async_setup_entry` in `sensor.py`:

```python
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wiener Netze sensors from config entry."""
    coordinator: WienerNetzeDataCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    sensors: list[SensorEntity] = []

    for meter_point in coordinator.meter_points:
        meter_id = meter_point["zaehlpunktnummer"]

        sensors.extend(
            [
                WienerNetzeCurrentPowerSensor(coordinator, meter_id),
                WienerNetzeDailyEnergySensor(coordinator, meter_id),
                WienerNetzeMonthlyEnergySensor(coordinator, meter_id),
                WienerNetzeYearlyEnergySensor(coordinator, meter_id),
                WienerNetzeMeterReadingSensor(coordinator, meter_id),
            ]
        )

    _LOGGER.debug("Adding %d sensors", len(sensors))
    async_add_entities(sensors)
```

## Acceptance Criteria

- [ ] Monthly energy sensor implemented
- [ ] Yearly energy sensor implemented
- [ ] Meter reading sensor implemented
- [ ] Proper state classes used
- [ ] Sensors reset appropriately
- [ ] All tests passing
- [ ] Sensors appear in UI

## Testing

```bash
# Run sensor tests
pytest tests/test_sensor.py -v

# Test in Home Assistant
# Verify all 5 sensors per meter appear
```

## References

- [Sensor State Classes](https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes)

## Notes

- Use TOTAL for monthly/yearly (resets each period)
- Use TOTAL_INCREASING for meter reading (never resets)
- Consider fetching historical data for accurate monthly/yearly totals
- Add reset logic for monthly/yearly sensors

## Next Task

→ **Task 17:** Historical Data Integration
