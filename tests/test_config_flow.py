"""Tests for config_flow.py."""
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from unittest.mock import AsyncMock, patch

from custom_components.wiener_netze.const import (
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
)
from tests.utils import load_json_fixture


async def test_form_user_step(hass: HomeAssistant):
    """Test user step form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_success_single_meter(hass: HomeAssistant):
    """Test successful setup with single meter point."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client.get_meter_points = AsyncMock(
            return_value=load_json_fixture("meter_points.json")["items"][:1]
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"]
        assert result["data"][CONF_CLIENT_ID] == "test_client"
        assert result["data"][CONF_CLIENT_SECRET] == "test_secret"
        assert result["data"][CONF_API_KEY] == "test_key"
        assert "meter_points" in result["data"]


async def test_form_user_invalid_auth(hass: HomeAssistant):
    """Test invalid authentication."""
    from custom_components.wiener_netze.api import WienerNetzeAuthError

    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeAuthError("Invalid credentials")
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "bad_client",
                CONF_CLIENT_SECRET: "bad_secret",
                CONF_API_KEY: "bad_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "invalid_auth"}


async def test_form_user_cannot_connect(hass: HomeAssistant):
    """Test connection error."""
    from custom_components.wiener_netze.api import WienerNetzeConnectionError

    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeConnectionError("Connection failed")
        )
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_user_unknown_error(hass: HomeAssistant):
    """Test unknown error."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(side_effect=Exception("Unknown error"))
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_form_no_meter_points(hass: HomeAssistant):
    """Test no meter points found."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client.get_meter_points = AsyncMock(return_value=[])
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "no_meter_points"}


async def test_form_multiple_meters(hass: HomeAssistant):
    """Test setup with multiple meter points."""
    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        meter_points = load_json_fixture("meter_points.json")["items"]
        mock_client.get_meter_points = AsyncMock(return_value=meter_points)
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        # Should show meter point selection
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "meter_point"

        # Select first meter point
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"meter_point": meter_points[0]["zaehlpunktnummer"]},
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"]
        assert result["data"]["meter_points"][0] == meter_points[0]


async def test_duplicate_meter_point(hass: HomeAssistant, mock_config_entry):
    """Test that duplicate meter points are rejected."""
    # Add existing config entry
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.wiener_netze.config_flow.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        # Return same meter point as in mock_config_entry (same unique_id)
        meter_points = [
            {
                "zaehlpunktnummer": "AT0000000000000000000000000000001",
                "verbrauchsstelle": {"strasse": "Test", "ort": "Wien"},
            }
        ]
        mock_client.get_meter_points = AsyncMock(return_value=meter_points)
        mock_client_class.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: "test_client",
                CONF_CLIENT_SECRET: "test_secret",
                CONF_API_KEY: "test_key",
            },
        )

        assert result["type"] == data_entry_flow.FlowResultType.ABORT
        assert result["reason"] == "already_configured"
