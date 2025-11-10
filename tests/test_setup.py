"""Test integration setup."""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState

from custom_components.wiener_netze.const import DOMAIN


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test setting up config entry."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api_client,
):
    """Test unloading config entry."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert DOMAIN not in hass.data


async def test_setup_entry_auth_failure(
    hass: HomeAssistant, mock_config_entry, mock_api_client
):
    """Test setup fails with authentication error."""
    mock_api_client.authenticate.side_effect = Exception("Auth failed")

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert not result
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR
