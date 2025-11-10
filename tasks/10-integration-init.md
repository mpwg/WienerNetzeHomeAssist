# Task 10: Integration Entry Point (**init**.py)

**Category:** Home Assistant Integration Core
**Priority:** Critical
**Estimated Effort:** 3-4 hours
**Status:** Not Started

## Description

Implement the integration entry point in `__init__.py`. This is the core file that initializes the integration when a user adds it in Home Assistant.

## Prerequisites

- **Task 07** completed (API Client - Consumption Data Retrieval)
- **Task 12** completed (Data Update Coordinator)
- Understanding of Home Assistant platform setup

## Objectives

1. Implement `async_setup_entry()` for integration initialization
2. Implement `async_unload_entry()` for clean shutdown
3. Create API client instance from config entry
4. Initialize data coordinator
5. Forward setup to sensor platform
6. Handle setup errors gracefully

## Deliverables

- [ ] `async_setup_entry()` implementation
- [ ] `async_unload_entry()` implementation
- [ ] API client initialization
- [ ] Coordinator setup
- [ ] Platform forwarding
- [ ] Unit tests for setup/teardown

## Implementation

### 1. Update **init**.py

```python
"""The Wiener Netze Smart Meter integration."""
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    WienerNetzeApiClient,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
)
from .const import CONF_API_KEY, CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN
from .coordinator import WienerNetzeDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wiener Netze Smart Meter from a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if setup was successful

    Raises:
        ConfigEntryAuthFailed: Authentication failed
        ConfigEntryNotReady: API not reachable

    """
    _LOGGER.debug("Setting up Wiener Netze Smart Meter integration")

    # Get credentials from config entry
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    api_key = entry.data[CONF_API_KEY]

    # Create API client
    session = async_get_clientsession(hass)
    api_client = WienerNetzeApiClient(
        session=session,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
    )

    # Test authentication
    try:
        await api_client.authenticate()
        _LOGGER.info("Successfully authenticated with Wiener Netze API")
    except WienerNetzeAuthError as err:
        _LOGGER.error("Authentication failed: %s", err)
        raise ConfigEntryAuthFailed from err
    except WienerNetzeConnectionError as err:
        _LOGGER.error("Connection failed: %s", err)
        raise ConfigEntryNotReady from err

    # Create coordinator
    coordinator = WienerNetzeDataCoordinator(hass, api_client, entry)

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except Exception as err:
        _LOGGER.error("Failed to fetch initial data: %s", err)
        raise ConfigEntryNotReady from err

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Wiener Netze Smart Meter integration setup complete")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    Returns:
        True if unload was successful

    """
    _LOGGER.debug("Unloading Wiener Netze Smart Meter integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )

    # Remove coordinator from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("Wiener Netze Smart Meter integration unloaded")

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry

    """
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
```

### 2. Update Constants

Add to `const.py`:

```python
# Home Assistant
DOMAIN = "wiener_netze"

# Configuration Keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_KEY = "api_key"
CONF_METER_POINTS = "meter_points"
```

### 3. Update Manifest

Ensure `manifest.json` has correct configuration:

```json
{
  "domain": "wiener_netze",
  "name": "Wiener Netze Smart Meter",
  "codeowners": ["@mpwg"],
  "config_flow": true,
  "documentation": "https://github.com/mpwg/WienerNetzeHomeAssist",
  "integration_type": "hub",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/mpwg/WienerNetzeHomeAssist/issues",
  "requirements": ["aiohttp>=3.9.0", "python-dateutil>=2.8.0"],
  "version": "0.1.0"
}
```

### 4. Create Unit Tests

Update `tests/test_init.py`:

```python
"""Tests for __init__.py."""
import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
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
    ) as mock_coordinator_class:
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.authenticate = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_coordinator = MagicMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

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


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test unloading entry."""
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
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator

        mock_config_entry.add_to_hass(hass)

        # Setup
        assert await async_setup_entry(hass, mock_config_entry)

        # Verify setup
        assert mock_config_entry.entry_id in hass.data[DOMAIN]

        # Unload
        assert await async_unload_entry(hass, mock_config_entry)

        # Verify cleanup
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_reload_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
):
    """Test reloading entry."""
    with patch(
        "custom_components.wiener_netze.async_setup_entry"
    ) as mock_setup, patch(
        "custom_components.wiener_netze.async_unload_entry"
    ) as mock_unload:
        mock_setup.return_value = True
        mock_unload.return_value = True

        mock_config_entry.add_to_hass(hass)

        await async_reload_entry(hass, mock_config_entry)

        mock_unload.assert_called_once()
        mock_setup.assert_called_once()
```

## Acceptance Criteria

- [ ] `async_setup_entry()` successfully initializes integration
- [ ] API client created from config entry data
- [ ] Authentication tested during setup
- [ ] Coordinator created and initial data fetched
- [ ] Platforms forwarded correctly
- [ ] `async_unload_entry()` cleans up resources
- [ ] Authentication errors raise `ConfigEntryAuthFailed`
- [ ] Connection errors raise `ConfigEntryNotReady`
- [ ] All tests passing
- [ ] Integration loads in Home Assistant

## Testing

```bash
# Run init tests
pytest tests/test_init.py -v

# Run all tests
pytest tests/ -v

# Test in Home Assistant
# 1. Copy integration to config/custom_components/
# 2. Restart Home Assistant
# 3. Check logs for errors
```

## References

- [Home Assistant Integration Setup](https://developers.home-assistant.io/docs/creating_integration_manifest)
- [Config Entry Setup](https://developers.home-assistant.io/docs/config_entries_index)

## Notes

- `ConfigEntryAuthFailed`: Triggers reauth flow
- `ConfigEntryNotReady`: Triggers retry
- Store coordinator in `hass.data[DOMAIN][entry.entry_id]`
- Use `async_get_clientsession()` for aiohttp session
- Forward to all platforms in `PLATFORMS` list

## Next Task

→ **Task 11:** Config Flow Implementation
