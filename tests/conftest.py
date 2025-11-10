"""Pytest configuration and fixtures for Wiener Netze Smart Meter tests."""

import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.wiener_netze.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Wiener Netze Smart Meter",
        data={
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "api_key": "test_api_key",
        },
        unique_id="AT0000000000000000000000000000001",
    )


@pytest.fixture
def mock_api_client():
    """Return a mock API client."""
    with patch(
        "custom_components.wiener_netze.api.WienerNetzeApiClient", create=True
    ) as mock_client:
        client = mock_client.return_value
        client.authenticate.return_value = True
        client.get_meter_points.return_value = [
            {
                "zaehlpunktnummer": "AT0000000000000000000000000000001",
                "geraet": {"geraetenummer": "12345678"},
            }
        ]
        client.get_consumption.return_value = {
            "messwert": 1234.5,
            "qualitaet": "VAL",
            "zeitVon": "2025-11-10T00:00:00",
            "zeitBis": "2025-11-10T00:15:00",
            "obisCode": "1-1:1.8.0",
        }
        yield client


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Set up the integration."""
    mock_config_entry.add_to_hass(hass)

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    yield


@pytest.fixture
def mock_oauth_response():
    """Return mock OAuth2 token response."""
    return {
        "access_token": "test_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@pytest.fixture
def mock_meter_data():
    """Return mock meter data."""
    return {
        "zaehlpunktnummer": "AT0000000000000000000000000000001",
        "geraet": {"geraetenummer": "12345678"},
        "anlage": {"anlagennummer": "AN123456"},
    }


@pytest.fixture
def mock_consumption_data():
    """Return mock consumption data."""
    return {
        "zaehlpunkt": "AT0000000000000000000000000000001",
        "wertetyp": "QUARTER_HOUR",
        "werte": [
            {
                "messwert": 0.25,
                "qualitaet": "VAL",
                "zeitVon": "2025-11-10T00:00:00",
                "zeitBis": "2025-11-10T00:15:00",
                "obisCode": "1-1:1.8.0",
            },
            {
                "messwert": 0.30,
                "qualitaet": "VAL",
                "zeitVon": "2025-11-10T00:15:00",
                "zeitBis": "2025-11-10T00:30:00",
                "obisCode": "1-1:1.8.0",
            },
        ],
    }
