# Task 06: API Client - Meter Points Retrieval

**Category:** API Client Development
**Priority:** High
**Estimated Effort:** 2-3 hours
**Status:** Not Started

## Description

Implement meter points (Zählpunkte) retrieval in the API client. This endpoint returns all smart meters associated with the authenticated account.

## Prerequisites

- **Task 05** completed (API Client - Basic Structure)
- OpenAPI specification reviewed (`dokumentation/Export_WN_SMART_METER_API.yaml`)

## Objectives

1. Implement `get_meter_points()` method
2. Parse and validate meter point data
3. Handle API-specific response format
4. Add comprehensive error handling
5. Create unit tests

## Deliverables

- [ ] `get_meter_points()` method in `api.py`
- [ ] Data model/type hints for meter point structure
- [ ] Unit tests for meter point retrieval
- [ ] Test fixtures for meter point responses

## API Endpoint Details

**Endpoint:** `GET /zaehlpunkte`

**Response Structure:**

```json
{
  "zaehlpunkte": [
    {
      "zaehlpunktnummer": "AT0010000000000000001000000000000",
      "adresse": {
        "strasse": "Musterstraße",
        "hausnummer": "1",
        "stiege": "1",
        "tuer": "10",
        "plz": "1010",
        "ort": "Wien"
      },
      "geschaeftspartner": "1234567890",
      "anlage": "000001"
    }
  ]
}
```

## Implementation

### 1. Add Data Models

Add to `api.py` or create `models.py`:

```python
from typing import TypedDict


class Address(TypedDict):
    """Address information."""
    strasse: str
    hausnummer: str
    stiege: str | None
    tuer: str | None
    plz: str
    ort: str


class MeterPoint(TypedDict):
    """Meter point (Zählpunkt) information."""
    zaehlpunktnummer: str
    adresse: Address
    geschaeftspartner: str
    anlage: str
```

### 2. Implement Method in WienerNetzeApiClient

```python
async def get_meter_points(self) -> list[MeterPoint]:
    """Get all meter points for the authenticated user.

    Returns:
        List of meter points with address and metadata

    Raises:
        WienerNetzeAuthError: Authentication failed
        WienerNetzeApiError: API request failed

    """
    _LOGGER.debug("Fetching meter points")

    try:
        response = await self._get("zaehlpunkte")

        meter_points = response.get("zaehlpunkte", [])

        _LOGGER.info(
            "Retrieved %d meter point(s)", len(meter_points)
        )

        return meter_points

    except WienerNetzeApiError:
        _LOGGER.error("Failed to fetch meter points")
        raise
```

### 3. Add Helper Methods

```python
def format_meter_point_address(meter_point: MeterPoint) -> str:
    """Format meter point address as string.

    Args:
        meter_point: Meter point data

    Returns:
        Formatted address string

    """
    addr = meter_point["adresse"]
    parts = [
        f"{addr['strasse']} {addr['hausnummer']}",
    ]

    if addr.get("stiege"):
        parts.append(f"Stiege {addr['stiege']}")

    if addr.get("tuer"):
        parts.append(f"Tür {addr['tuer']}")

    parts.append(f"{addr['plz']} {addr['ort']}")

    return ", ".join(parts)


def get_meter_point_id(meter_point: MeterPoint) -> str:
    """Get unique identifier for meter point.

    Args:
        meter_point: Meter point data

    Returns:
        Meter point number (Zählpunktnummer)

    """
    return meter_point["zaehlpunktnummer"]
```

### 4. Update Test Fixtures

Add `tests/fixtures/meter_points.json`:

```json
{
  "zaehlpunkte": [
    {
      "zaehlpunktnummer": "AT0010000000000000001000000000001",
      "adresse": {
        "strasse": "Teststraße",
        "hausnummer": "42",
        "stiege": "2",
        "tuer": "15",
        "plz": "1010",
        "ort": "Wien"
      },
      "geschaeftspartner": "1234567890",
      "anlage": "000001"
    },
    {
      "zaehlpunktnummer": "AT0010000000000000001000000000002",
      "adresse": {
        "strasse": "Beispielgasse",
        "hausnummer": "10",
        "stiege": null,
        "tuer": null,
        "plz": "1020",
        "ort": "Wien"
      },
      "geschaeftspartner": "1234567890",
      "anlage": "000002"
    }
  ]
}
```

### 5. Create Unit Tests

Add to `tests/test_api.py`:

```python
class TestMeterPoints:
    """Tests for meter point retrieval."""

    async def test_get_meter_points_success(self, api_client, mock_session):
        """Test successful meter points retrieval."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        meter_points_data = load_json_fixture("meter_points.json")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=meter_points_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client.get_meter_points()

        assert len(result) == 2
        assert result[0]["zaehlpunktnummer"] == "AT0010000000000000001000000000001"
        assert result[0]["adresse"]["strasse"] == "Teststraße"
        assert result[1]["adresse"]["plz"] == "1020"

    async def test_get_meter_points_empty(self, api_client, mock_session):
        """Test meter points retrieval with no meters."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"zaehlpunkte": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client.get_meter_points()

        assert len(result) == 0

    async def test_get_meter_points_auth_error(self, api_client, mock_session):
        """Test meter points retrieval with auth error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeAuthError):
            await api_client.get_meter_points()

    def test_format_meter_point_address_full(self):
        """Test formatting full address."""
        meter_point = {
            "adresse": {
                "strasse": "Teststraße",
                "hausnummer": "42",
                "stiege": "2",
                "tuer": "15",
                "plz": "1010",
                "ort": "Wien",
            }
        }

        result = format_meter_point_address(meter_point)

        assert result == "Teststraße 42, Stiege 2, Tür 15, 1010 Wien"

    def test_format_meter_point_address_minimal(self):
        """Test formatting minimal address."""
        meter_point = {
            "adresse": {
                "strasse": "Beispielgasse",
                "hausnummer": "10",
                "stiege": None,
                "tuer": None,
                "plz": "1020",
                "ort": "Wien",
            }
        }

        result = format_meter_point_address(meter_point)

        assert result == "Beispielgasse 10, 1020 Wien"

    def test_get_meter_point_id(self):
        """Test getting meter point ID."""
        meter_point = {
            "zaehlpunktnummer": "AT0010000000000000001000000000001"
        }

        result = get_meter_point_id(meter_point)

        assert result == "AT0010000000000000001000000000001"
```

## Acceptance Criteria

- [ ] `get_meter_points()` method implemented
- [ ] Returns list of meter points with correct structure
- [ ] Handles empty response (no meter points)
- [ ] Handles authentication errors
- [ ] Helper functions for address formatting and ID extraction
- [ ] All tests passing
- [ ] Code coverage >80%

## Testing

```bash
# Run meter points tests
pytest tests/test_api.py::TestMeterPoints -v

# Check coverage
pytest tests/test_api.py --cov=custom_components.wiener_netze.api --cov-report=term-missing
```

## References

- [Wiener Netze API Documentation](../dokumentation/Export_WN_SMART_METER_API.yaml)
- Endpoint: `/zaehlpunkte`

## Notes

- Zählpunktnummer is the unique identifier (33 characters)
- Some address fields (stiege, tuer) may be null
- geschaeftspartner is the customer number
- anlage is the facility/installation number

## Next Task

→ **Task 07:** API Client - Consumption Data Retrieval
