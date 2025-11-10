# Task 12 Completion: Data Update Coordinator

**Date:** November 10, 2025
**Status:** ✅ Complete

## Overview

Successfully implemented the `WienerNetzeDataCoordinator` class to manage periodic data fetching from the Wiener Netze Smart Meter API and provide data to sensor entities.

## Implementation Details

### Core Functionality

The coordinator is implemented in `custom_components/wiener_netze/coordinator.py` and includes:

1. **Data Update Coordinator Class**

   - Extends Home Assistant's `DataUpdateCoordinator`
   - Fetches data every 15 minutes (configurable via `DEFAULT_SCAN_INTERVAL`)
   - Manages multiple meter points simultaneously
   - Stores structured data for easy sensor access

2. **Main Methods**
   - `_async_update_data()`: Fetches consumption data for all configured meter points
   - `get_meter_data(meter_id)`: Retrieves all data for a specific meter point
   - `get_latest_reading(meter_id)`: Gets the most recent consumption reading
   - `get_total_consumption_today(meter_id)`: Calculates total daily consumption

### Error Handling

The coordinator implements comprehensive error handling:

- **Authentication Errors**: Raises `ConfigEntryAuthFailed` to trigger re-authentication flow
- **Connection Errors**: Raises `UpdateFailed` with connection error details (will retry)
- **API Errors**: Raises `UpdateFailed` with API error information
- **Unexpected Errors**: Catches and wraps all other exceptions in `UpdateFailed`

All errors are properly logged with appropriate log levels (ERROR, WARNING, DEBUG).

### Data Structure

The coordinator stores data in a dictionary format:

```python
{
    "meter_id": {
        "meter_point": {...},  # Meter point metadata
        "consumption": {...},  # Consumption data with zaehlwerke
        "last_update": float,  # Timestamp of last update
    }
}
```

### Configuration

Added `CONF_METER_POINTS` constant to `const.py` for consistent configuration key usage:

```python
CONF_METER_POINTS = "meter_points"
```

## Testing

### Test Suite

Implemented comprehensive test coverage in `tests/test_coordinator.py` with 18 tests:

1. **Initialization Tests**

   - Coordinator initialization with proper configuration

2. **Update Tests**

   - Successful data updates for single and multiple meters
   - Authentication error handling
   - Connection error handling
   - API error handling
   - Unexpected error handling
   - Empty meter points handling

3. **Data Access Tests**
   - Getting meter data for existing meters
   - Handling non-existent meters
   - Handling empty coordinator data
   - Getting latest readings with various data states
   - Calculating total consumption

### Test Results

```bash
✅ 18/18 tests passing (100% pass rate)
```

All tests verify:

- Proper data fetching and storage
- Error handling and exception raising
- Data access methods returning correct values
- Edge cases (empty data, missing meters, etc.)

### Test Coverage

The test suite covers:

- ✅ Normal operation flow
- ✅ All error scenarios
- ✅ Data structure edge cases
- ✅ Multiple meter points
- ✅ Empty readings handling
- ✅ Helper method functionality

## Key Features

1. **Automatic Updates**: Fetches data every 15 minutes
2. **Multi-Meter Support**: Handles multiple meter points in single update
3. **Error Recovery**: Proper exception handling with retry capability
4. **Efficient Data Access**: Helper methods for common data queries
5. **Logging**: Comprehensive logging for debugging and monitoring
6. **Home Assistant Integration**: Follows HA best practices for coordinators

## Files Modified

1. **custom_components/wiener_netze/coordinator.py**

   - Enhanced `_async_update_data()` to work with API response structure
   - Updated helper methods to handle `zaehlwerke` data structure
   - Fixed import to include `CONF_METER_POINTS`

2. **custom_components/wiener_netze/const.py**

   - Added `CONF_METER_POINTS` constant

3. **tests/test_coordinator.py**

   - Implemented complete test suite with 18 comprehensive tests
   - Added helper function `create_mock_config_entry()` for test data
   - Fixed test assertions to work with coordinator exception handling

4. **tests/conftest.py**
   - Simplified `mock_config_entry` fixture to remove meter_points default

## Technical Decisions

1. **Update Interval**: Set to 15 minutes to balance data freshness with API rate limits
2. **Error Handling**: Authentication errors trigger reauth flow, other errors allow retry
3. **Data Structure**: Nested dictionary keyed by meter_id for O(1) lookups
4. **Helper Methods**: Provide convenient access patterns for sensor entities
5. **Test Approach**: Use `create_mock_config_entry()` helper to avoid immutability issues

## Integration Points

### With API Client (`api.py`)

- Calls `get_consumption_data()` for each meter point
- Handles all API exceptions appropriately

### With Config Flow (`config_flow.py`)

- Reads meter points from config entry data
- Uses `CONF_METER_POINTS` constant

### With Sensors (Future Task 15)

- Provides `get_meter_data()` for full meter information
- Provides `get_latest_reading()` for current values
- Provides `get_total_consumption_today()` for daily totals

## API Usage

The coordinator fetches data using:

- **Endpoint**: `/zaehlpunkte/{meter_id}/messwerte`
- **Granularity**: `QUARTER_HOUR` (15-minute intervals)
- **Date Range**: Today's date (from midnight to now)

## Next Steps

With the coordinator implemented, the next task is:

→ **Task 15: Sensor Platform Implementation**

The coordinator is now ready to provide data to sensor entities that will expose:

- Current consumption
- Total daily consumption
- Latest reading timestamp
- Meter point information

## Verification

✅ All acceptance criteria met:

- [x] Coordinator fetches data from API
- [x] Updates every 15 minutes (configurable)
- [x] Handles authentication errors (raises ConfigEntryAuthFailed)
- [x] Handles connection errors (raises UpdateFailed)
- [x] Stores data for all meter points
- [x] Provides helper methods for sensor access
- [x] All tests passing (18/18)
- [x] Code follows Home Assistant best practices

## Notes

- The coordinator properly handles the Wiener Netze API response structure with `zaehlwerke` containing `messwerte`
- Test suite uses `pytest.approx()` for float comparisons to avoid precision issues
- Exception handling uses coordinator's built-in mechanism (checks `last_exception` and `last_update_success`)
- Logging provides good visibility into update process for debugging

---

**Implementation completed successfully!** 🎉
