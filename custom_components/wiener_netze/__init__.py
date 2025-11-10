"""The Wiener Netze Smart Meter integration."""
import logging

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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

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
