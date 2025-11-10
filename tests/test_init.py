"""Tests for __init__.py."""
import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.wiener_netze import (
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
)
from custom_components.wiener_netze.api import (
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
)
from custom_components.wiener_netze.const import DOMAIN


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test successful setup."""
    with patch(
        "custom_components.wiener_netze.WienerNetzeApiClient"
    ) as mock_client_class, patch(
        "custom_components.wiener_netze.WienerNetzeDataCoordinator"
    ) as mock_coordinator_class, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
    ) as mock_forward:
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        mock_forward.return_value = None

        mock_config_entry.add_to_hass(hass)

        # Setup should succeed
        assert await async_setup_entry(hass, mock_config_entry)

        # Verify API client was created and authenticated
        mock_client_class.assert_called_once()
        mock_client.authenticate.assert_called_once()

        # Verify coordinator was created and refreshed
        mock_coordinator_class.assert_called_once()
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()

        # Verify coordinator stored in hass.data
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Verify platforms were forwarded
        mock_forward.assert_called_once()


async def test_setup_entry_auth_failed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test setup with authentication failure."""
    with patch(
        "custom_components.wiener_netze.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeAuthError("Invalid credentials")
        )
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)

        # Setup should raise ConfigEntryAuthFailed
        with pytest.raises(ConfigEntryAuthFailed):
            await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_connection_failed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test setup with connection failure."""
    with patch(
        "custom_components.wiener_netze.WienerNetzeApiClient"
    ) as mock_client_class:
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock(
            side_effect=WienerNetzeConnectionError("Connection failed")
        )
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)

        # Setup should raise ConfigEntryNotReady
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_first_refresh_failed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test setup when first refresh fails."""
    with patch(
        "custom_components.wiener_netze.WienerNetzeApiClient"
    ) as mock_client_class, patch(
        "custom_components.wiener_netze.WienerNetzeDataCoordinator"
    ) as mock_coordinator_class:
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock(
            side_effect=Exception("API error")
        )
        mock_coordinator_class.return_value = mock_coordinator

        mock_config_entry.add_to_hass(hass)

        # Setup should raise ConfigEntryNotReady
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test unloading entry."""
    with patch(
        "custom_components.wiener_netze.WienerNetzeApiClient"
    ) as mock_client_class, patch(
        "custom_components.wiener_netze.WienerNetzeDataCoordinator"
    ) as mock_coordinator_class, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
    ) as mock_forward, patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload_platforms:
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        mock_forward.return_value = None
        mock_unload_platforms.return_value = True

        mock_config_entry.add_to_hass(hass)

        # Setup
        assert await async_setup_entry(hass, mock_config_entry)

        # Verify setup
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Unload
        assert await async_unload_entry(hass, mock_config_entry)

        # Verify cleanup
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]

        # Verify unload was called
        mock_unload_platforms.assert_called_once()


async def test_reload_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test reloading entry."""
    with patch("custom_components.wiener_netze.async_setup_entry") as mock_setup, patch(
        "custom_components.wiener_netze.async_unload_entry"
    ) as mock_unload:
        mock_setup.return_value = True
        mock_unload.return_value = True

        mock_config_entry.add_to_hass(hass)

        await async_reload_entry(hass, mock_config_entry)

        mock_unload.assert_called_once()
        mock_setup.assert_called_once()
