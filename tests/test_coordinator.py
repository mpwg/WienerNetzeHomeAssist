"""Tests for coordinator.py."""
import pytest
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from unittest.mock import AsyncMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wiener_netze.coordinator import (
    WienerNetzeDataCoordinator,
)
from custom_components.wiener_netze.api import (
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
    WienerNetzeApiError,
)
from custom_components.wiener_netze.const import DOMAIN, CONF_METER_POINTS
from tests.utils import load_json_fixture


def create_mock_config_entry(meter_points=None):
    """Create a mock config entry with optional meter points."""
    data = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "api_key": "test_api_key",
    }
    if meter_points is not None:
        data[CONF_METER_POINTS] = meter_points

    return MockConfigEntry(
        domain=DOMAIN,
        title="Wiener Netze Smart Meter",
        data=data,
        unique_id="AT0000000000000000000000000000001",
    )


async def test_coordinator_initialization(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test coordinator initialization."""
    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, mock_config_entry)

    assert coordinator.hass == hass
    assert coordinator.api_client == mock_api_client
    assert coordinator.config_entry == mock_config_entry
    assert coordinator.name == "wiener_netze"
    assert coordinator.update_interval == timedelta(minutes=15)


async def test_coordinator_update_success(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test successful coordinator update."""
    # Setup mock data
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    # Create coordinator
    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    # Update data
    await coordinator.async_refresh()

    # Verify data
    assert coordinator.data
    meter_id = meter_points[0]["zaehlpunktnummer"]
    assert meter_id in coordinator.data
    assert coordinator.data[meter_id]["consumption"] == consumption_data
    assert coordinator.data[meter_id]["meter_point"] == meter_points[0]


async def test_coordinator_update_multiple_meters(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator update with multiple meter points."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    # Verify data for all meter points
    assert len(coordinator.data) == len(meter_points)
    for meter_point in meter_points:
        meter_id = meter_point["zaehlpunktnummer"]
        assert meter_id in coordinator.data


async def test_coordinator_update_auth_error(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator update with auth error."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=WienerNetzeAuthError("Invalid credentials")
    )

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    # Should raise ConfigEntryAuthFailed
    # Note: async_refresh() catches exceptions, so we need to check last_exception
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, ConfigEntryAuthFailed)


async def test_coordinator_update_connection_error(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator update with connection error."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=WienerNetzeConnectionError("Connection failed")
    )

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    # Should raise UpdateFailed
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert "Connection error" in str(coordinator.last_exception)


async def test_coordinator_update_api_error(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator update with API error."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=WienerNetzeApiError("API error")
    )

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    # Should raise UpdateFailed
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert "API error" in str(coordinator.last_exception)


async def test_coordinator_update_unexpected_error(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator update with unexpected error."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(
        side_effect=Exception("Unexpected error")
    )

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    # Should raise UpdateFailed
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert "Unexpected error" in str(coordinator.last_exception)


async def test_get_meter_data(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting meter data."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    meter_data = coordinator.get_meter_data(meter_id)

    assert meter_data
    assert meter_data["meter_point"] == meter_points[0]
    assert meter_data["consumption"] == consumption_data
    assert "last_update" in meter_data


async def test_get_meter_data_not_found(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting meter data for non-existent meter."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_data = coordinator.get_meter_data("NONEXISTENT")
    assert meter_data is None


async def test_get_meter_data_no_data(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting meter data when coordinator has no data."""
    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, mock_config_entry)

    # Don't call async_refresh, so coordinator.data is None
    meter_data = coordinator.get_meter_data("AT0010000000000000001000000000001")
    assert meter_data is None


async def test_get_latest_reading(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting latest reading."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    latest = coordinator.get_latest_reading(meter_id)

    assert latest
    # Should be the last reading from the fixture
    expected_reading = consumption_data["zaehlwerke"][0]["messwerte"][-1]
    assert latest == expected_reading
    assert latest["messwert"] == 0.18


async def test_get_latest_reading_no_data(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting latest reading when no data available."""
    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, mock_config_entry)

    latest = coordinator.get_latest_reading("AT0010000000000000001000000000001")
    assert latest is None


async def test_get_latest_reading_no_zaehlwerke(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting latest reading when no Zählwerke in data."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = {
        "zaehlpunkt": "AT0010000000000000001000000000001",
        "zaehlwerke": [],
    }

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    latest = coordinator.get_latest_reading(meter_id)
    assert latest is None


async def test_get_latest_reading_no_messwerte(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting latest reading when no Messwerte in Zählwerk."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = {
        "zaehlpunkt": "AT0010000000000000001000000000001",
        "zaehlwerke": [{"obisCode": "1-1:1.8.0", "einheit": "kWh", "messwerte": []}],
    }

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    latest = coordinator.get_latest_reading(meter_id)
    assert latest is None


async def test_get_total_consumption_today(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting total consumption."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = load_json_fixture("consumption_quarter_hour.json")

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    total = coordinator.get_total_consumption_today(meter_id)

    # Sum of values from fixture: 0.15 + 0.12 + 0.18 = 0.45
    assert total == pytest.approx(0.45)


async def test_get_total_consumption_today_no_data(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test getting total consumption when no data available."""
    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, mock_config_entry)

    total = coordinator.get_total_consumption_today("AT0010000000000000001000000000001")
    assert total == 0.0


async def test_get_total_consumption_today_empty_readings(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test getting total consumption when readings are empty."""
    meter_points_data = load_json_fixture("meter_points.json")
    meter_points = meter_points_data.get("items", meter_points_data)
    consumption_data = {
        "zaehlpunkt": "AT0010000000000000001000000000001",
        "zaehlwerke": [{"obisCode": "1-1:1.8.0", "einheit": "kWh", "messwerte": []}],
    }

    config_entry = create_mock_config_entry(meter_points)
    mock_api_client.get_consumption_data = AsyncMock(return_value=consumption_data)

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    meter_id = meter_points[0]["zaehlpunktnummer"]
    total = coordinator.get_total_consumption_today(meter_id)
    assert total == 0.0


async def test_coordinator_empty_meter_points(
    hass: HomeAssistant,
    mock_api_client,
):
    """Test coordinator with empty meter points."""
    config_entry = create_mock_config_entry([])

    coordinator = WienerNetzeDataCoordinator(hass, mock_api_client, config_entry)

    await coordinator.async_refresh()

    assert coordinator.data == {}
