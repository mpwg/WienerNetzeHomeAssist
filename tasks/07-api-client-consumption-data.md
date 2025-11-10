# Task 07: API Client - Consumption Data Retrieval

**Category:** API Client Development
**Priority:** High
**Estimated Effort:** 3-4 hours
**Status:** Not Started

## Description

Implement consumption data retrieval in the API client. This endpoint returns smart meter readings with different granularities (15-minute intervals, daily, meter readings).

## Prerequisites

- **Task 06** completed (API Client - Meter Points Retrieval)
- Understanding of Wiener Netze data granularities

## Objectives

1. Implement `get_consumption_data()` method
2. Support all granularity types (QUARTER_HOUR, DAY, METER_READ)
3. Parse and validate consumption data
4. Handle date range parameters
5. Add comprehensive unit tests

## Deliverables

- [ ] `get_consumption_data()` method in `api.py`
- [ ] Data models for consumption data structure
- [ ] Date range handling
- [ ] Unit tests with multiple granularities
- [ ] Test fixtures for consumption responses

## API Endpoint Details

**Endpoint:** `GET /messdaten/zaehlpunkt/{zaehlpunkt}`

**Query Parameters:**

- `dateFrom`: Start date (YYYY-MM-DD)
- `dateTo`: End date (YYYY-MM-DD)
- `granularity`: QUARTER_HOUR | DAY | METER_READ
- `wertetyp`: SMART_METER | ALL (default: SMART_METER)

**Response Structure:**

```json
{
  "zaehlpunkt": "AT0010000000000000001000000000001",
  "messwerte": [
    {
      "zeitpunktVon": "2024-11-10T00:00:00.000+01:00",
      "zeitpunktBis": "2024-11-10T00:15:00.000+01:00",
      "wert": 0.15,
      "qualitaet": "VAL"
    }
  ]
}
```

## Implementation

### 1. Add Data Models

```python
from datetime import datetime
from typing import TypedDict


class ConsumptionReading(TypedDict):
    """Single consumption reading."""
    zeitpunktVon: str  # ISO 8601 timestamp
    zeitpunktBis: str  # ISO 8601 timestamp
    wert: float  # kWh
    qualitaet: str  # VAL (validated) or EST (estimated)


class ConsumptionData(TypedDict):
    """Consumption data response."""
    zaehlpunkt: str
    messwerte: list[ConsumptionReading]
```

### 2. Implement Method in WienerNetzeApiClient

```python
async def get_consumption_data(
    self,
    meter_point: str,
    date_from: str,
    date_to: str,
    granularity: str = GRANULARITY_QUARTER_HOUR,
) -> ConsumptionData:
    """Get consumption data for a meter point.

    Args:
        meter_point: Meter point number (Zählpunktnummer)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        granularity: Data granularity (QUARTER_HOUR, DAY, METER_READ)

    Returns:
        Consumption data with readings

    Raises:
        WienerNetzeNotFoundError: Meter point not found
        WienerNetzeApiError: API request failed

    """
    _LOGGER.debug(
        "Fetching consumption data for %s from %s to %s (granularity: %s)",
        meter_point,
        date_from,
        date_to,
        granularity,
    )

    endpoint = f"messdaten/zaehlpunkt/{meter_point}"
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "granularity": granularity,
        "wertetyp": RESULT_TYPE_SMART_METER,
    }

    try:
        response = await self._get(endpoint, params=params)

        readings = response.get("messwerte", [])

        _LOGGER.info(
            "Retrieved %d reading(s) for meter point %s",
            len(readings),
            meter_point,
        )

        return response

    except WienerNetzeNotFoundError:
        _LOGGER.error("Meter point not found: %s", meter_point)
        raise
    except WienerNetzeApiError:
        _LOGGER.error("Failed to fetch consumption data")
        raise
```

### 3. Add Helper Methods

```python
from datetime import date, timedelta


def get_date_range_for_today() -> tuple[str, str]:
    """Get date range for today.

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    today = date.today()
    return today.isoformat(), today.isoformat()


def get_date_range_for_yesterday() -> tuple[str, str]:
    """Get date range for yesterday.

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    yesterday = date.today() - timedelta(days=1)
    return yesterday.isoformat(), yesterday.isoformat()


def get_date_range_for_last_days(days: int) -> tuple[str, str]:
    """Get date range for the last N days.

    Args:
        days: Number of days to include

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    today = date.today()
    start = today - timedelta(days=days - 1)
    return start.isoformat(), today.isoformat()


def parse_consumption_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp from API.

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Parsed datetime object

    """
    # Handle format: "2024-11-10T00:00:00.000+01:00"
    from dateutil import parser

    return parser.isoparse(timestamp)


def calculate_total_consumption(readings: list[ConsumptionReading]) -> float:
    """Calculate total consumption from readings.

    Args:
        readings: List of consumption readings

    Returns:
        Total consumption in kWh

    """
    return sum(reading["wert"] for reading in readings)


def get_validated_readings(
    readings: list[ConsumptionReading],
) -> list[ConsumptionReading]:
    """Filter readings to only validated values.

    Args:
        readings: List of consumption readings

    Returns:
        List of validated readings (quality=VAL)

    """
    return [r for r in readings if r["qualitaet"] == QUALITY_VAL]
```

### 4. Update Constants

Add to `const.py`:

```python
# API Parameters
GRANULARITY_QUARTER_HOUR = "QUARTER_HOUR"
GRANULARITY_DAY = "DAY"
GRANULARITY_METER_READ = "METER_READ"

RESULT_TYPE_SMART_METER = "SMART_METER"
RESULT_TYPE_ALL = "ALL"

# Quality Indicators
QUALITY_VAL = "VAL"  # Validated actual value
QUALITY_EST = "EST"  # Estimated/calculated value
```

### 5. Update Test Fixtures

Add `tests/fixtures/consumption_quarter_hour.json`:

```json
{
  "zaehlpunkt": "AT0010000000000000001000000000001",
  "messwerte": [
    {
      "zeitpunktVon": "2024-11-10T00:00:00.000+01:00",
      "zeitpunktBis": "2024-11-10T00:15:00.000+01:00",
      "wert": 0.15,
      "qualitaet": "VAL"
    },
    {
      "zeitpunktVon": "2024-11-10T00:15:00.000+01:00",
      "zeitpunktBis": "2024-11-10T00:30:00.000+01:00",
      "wert": 0.12,
      "qualitaet": "VAL"
    },
    {
      "zeitpunktVon": "2024-11-10T00:30:00.000+01:00",
      "zeitpunktBis": "2024-11-10T00:45:00.000+01:00",
      "wert": 0.18,
      "qualitaet": "EST"
    }
  ]
}
```

### 6. Create Unit Tests

Add to `tests/test_api.py`:

```python
class TestConsumptionData:
    """Tests for consumption data retrieval."""

    async def test_get_consumption_data_quarter_hour(
        self, api_client, mock_session
    ):
        """Test consumption data retrieval with 15-minute intervals."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        consumption_data = load_json_fixture("consumption_quarter_hour.json")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=consumption_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client.get_consumption_data(
            meter_point="AT0010000000000000001000000000001",
            date_from="2024-11-10",
            date_to="2024-11-10",
            granularity=GRANULARITY_QUARTER_HOUR,
        )

        assert result["zaehlpunkt"] == "AT0010000000000000001000000000001"
        assert len(result["messwerte"]) == 3
        assert result["messwerte"][0]["wert"] == 0.15
        assert result["messwerte"][0]["qualitaet"] == "VAL"

    async def test_get_consumption_data_not_found(
        self, api_client, mock_session
    ):
        """Test consumption data retrieval with invalid meter point."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeNotFoundError):
            await api_client.get_consumption_data(
                meter_point="INVALID",
                date_from="2024-11-10",
                date_to="2024-11-10",
            )

    def test_calculate_total_consumption(self):
        """Test total consumption calculation."""
        readings = [
            {"wert": 0.15, "qualitaet": "VAL"},
            {"wert": 0.12, "qualitaet": "VAL"},
            {"wert": 0.18, "qualitaet": "EST"},
        ]

        total = calculate_total_consumption(readings)

        assert total == 0.45

    def test_get_validated_readings(self):
        """Test filtering validated readings."""
        readings = [
            {"wert": 0.15, "qualitaet": "VAL"},
            {"wert": 0.12, "qualitaet": "VAL"},
            {"wert": 0.18, "qualitaet": "EST"},
        ]

        validated = get_validated_readings(readings)

        assert len(validated) == 2
        assert all(r["qualitaet"] == "VAL" for r in validated)

    def test_get_date_range_for_today(self):
        """Test date range for today."""
        date_from, date_to = get_date_range_for_today()

        assert date_from == date_to
        assert len(date_from) == 10  # YYYY-MM-DD

    def test_get_date_range_for_last_days(self):
        """Test date range for last N days."""
        date_from, date_to = get_date_range_for_last_days(7)

        from_date = datetime.fromisoformat(date_from).date()
        to_date = datetime.fromisoformat(date_to).date()

        assert (to_date - from_date).days == 6
```

## Acceptance Criteria

- [ ] `get_consumption_data()` method implemented
- [ ] Supports all granularity types
- [ ] Date range parameters work correctly
- [ ] Returns consumption data with correct structure
- [ ] Handles invalid meter point (404)
- [ ] Helper functions for date ranges and calculations
- [ ] All tests passing
- [ ] Code coverage >80%

## Testing

```bash
# Run consumption data tests
pytest tests/test_api.py::TestConsumptionData -v

# Run all API tests
pytest tests/test_api.py -v

# Check coverage
pytest tests/test_api.py --cov=custom_components.wiener_netze.api --cov-report=term-missing
```

## References

- [Wiener Netze API Documentation](../dokumentation/Export_WN_SMART_METER_API.yaml)
- Endpoint: `/messdaten/zaehlpunkt/{zaehlpunkt}`

## Notes

- QUARTER_HOUR: 15-minute interval readings (96 per day)
- DAY: Daily totals
- METER_READ: Actual meter readings
- Quality indicator:
  - VAL: Validated actual measurement
  - EST: Estimated/calculated value
- Timestamps are in ISO 8601 format with timezone
- Date range is inclusive

## Next Task

→ **Task 10:** Integration **init**.py (Entry Point)
