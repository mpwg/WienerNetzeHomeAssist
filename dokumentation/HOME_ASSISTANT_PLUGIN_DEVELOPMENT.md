# Home Assistant Custom Integration Development Guide

**Last Updated:** November 10, 2025
**For:** Wiener Netze Smart Meter Integration Project

---

## Table of Contents

1. [Introduction](#introduction)
2. [Home Assistant Architecture](#home-assistant-architecture)
3. [Integration Components](#integration-components)
4. [File Structure](#file-structure)
5. [manifest.json](#manifestjson)
6. [Entry Point (**init**.py)](#entry-point-__init__py)
7. [Config Flow](#config-flow)
8. [Data Update Coordinator](#data-update-coordinator)
9. [Sensor Platform](#sensor-platform)
10. [Translations](#translations)
11. [Testing](#testing)
12. [HACS Compatibility](#hacs-compatibility)
13. [Best Practices](#best-practices)
14. [Resources](#resources)

---

## Introduction

Home Assistant custom integrations (also called custom components) allow developers to extend Home Assistant's functionality by connecting to new devices, services, or APIs. This document provides a comprehensive guide for developing the Wiener Netze Smart Meter integration.

### What is a Custom Integration?

A custom integration is a Python package that:

- Lives in the `custom_components/<domain>/` directory
- Implements Home Assistant's integration API
- Can be configured via UI (config flow) or YAML
- Provides entities (sensors, switches, etc.) to Home Assistant
- Follows async/await patterns for non-blocking operations

### Integration vs Component

- **Integration**: The complete package that connects to an external service/device
- **Component**: A synonym for integration in Home Assistant terminology
- **Platform**: A specific entity type implementation (e.g., sensor, switch, light)

---

## Home Assistant Architecture

### Key Concepts

#### 1. Home Assistant Core (`hass`)

The central object that manages:

- State machine (all entity states)
- Event bus (system events)
- Service registry
- Configuration
- Data storage

#### 2. Config Entry

A configuration entry represents one configured instance of an integration:

- Created via config flow (UI setup)
- Stored persistently
- Can have multiple entries for the same integration
- Contains user-provided configuration data

#### 3. Entity

The basic building block:

- Represents a device, sensor, or service
- Has a unique entity ID (e.g., `sensor.meter_current_power`)
- Has a state and attributes
- Updates periodically or on events

#### 4. Device

Groups related entities:

- Represents a physical or logical device
- Multiple entities can belong to one device
- Tracked in the device registry
- Provides device information (manufacturer, model, etc.)

---

## Integration Components

### Minimal Requirements

1. **manifest.json** - Integration metadata
2. ****init**.py** - Entry point with setup functions
3. **Platform file** (e.g., sensor.py) - Entity implementation

### Recommended Components

4. **config_flow.py** - UI-based configuration
5. **coordinator.py** - Data update coordination
6. **const.py** - Constants and configuration keys
7. **api.py** - API client implementation
8. **strings.json** - UI strings (English)
9. **translations/** - Localized strings
10. **services.yaml** - Service definitions (if applicable)

---

## File Structure

### Basic Structure

```
custom_components/
└── wiener_netze/
    ├── __init__.py              # Entry point
    ├── manifest.json            # Integration metadata
    ├── config_flow.py           # UI configuration
    ├── const.py                 # Constants
    ├── api.py                   # API client
    ├── coordinator.py           # Data coordinator
    ├── sensor.py                # Sensor platform
    ├── strings.json             # English strings
    ├── services.yaml            # Service definitions (optional)
    └── translations/
        ├── en.json              # English translation
        ├── de.json              # German translation
        └── ...
```

### Where Home Assistant Looks for Integrations

1. `<config directory>/custom_components/<domain>/` (custom integrations)
2. `homeassistant/components/<domain>/` (built-in integrations)

**Note:** Custom integrations override built-in ones with the same domain (not recommended).

---

## manifest.json

The `manifest.json` file defines integration metadata.

### Required Fields

```json
{
  "domain": "wiener_netze",
  "name": "Wiener Netze Smart Meter",
  "version": "1.0.0",
  "documentation": "https://github.com/mpwg/WienerNetzeHomeAssist",
  "issue_tracker": "https://github.com/mpwg/WienerNetzeHomeAssist/issues",
  "codeowners": ["@mpwg"],
  "config_flow": true,
  "dependencies": [],
  "requirements": ["aiohttp>=3.8.0"],
  "iot_class": "cloud_polling",
  "integration_type": "hub"
}
```

### Field Descriptions

| Field              | Description                                         | Required |
| ------------------ | --------------------------------------------------- | -------- |
| `domain`           | Unique identifier (lowercase, underscores only)     | ✅ Yes   |
| `name`             | Display name in UI                                  | ✅ Yes   |
| `version`          | Semantic version (required for custom integrations) | ✅ Yes   |
| `documentation`    | Link to documentation                               | ✅ Yes   |
| `issue_tracker`    | Link to issue tracker                               | ✅ Yes   |
| `codeowners`       | GitHub usernames of maintainers                     | ✅ Yes   |
| `config_flow`      | Whether integration supports UI config              | ✅ Yes   |
| `dependencies`     | Other HA integrations this depends on               | ✅ Yes   |
| `requirements`     | Python packages (with versions)                     | ✅ Yes   |
| `iot_class`        | How integration communicates                        | ✅ Yes   |
| `integration_type` | Type of integration                                 | ✅ Yes   |

### IoT Class Options

- `cloud_polling` - Polls cloud API
- `cloud_push` - Cloud pushes updates
- `local_polling` - Polls local device
- `local_push` - Local device pushes updates
- `calculated` - No external communication

### Integration Types

- `hub` - Gateway to multiple devices/services (e.g., Philips Hue)
- `device` - Single device (e.g., ESPHome)
- `service` - Single service (e.g., DuckDNS)
- `helper` - Automation helper (e.g., input_boolean)
- `entity` - Basic entity platform (rarely used)
- `virtual` - Points to another integration/standard

**For Wiener Netze:** Use `hub` (provides access to multiple smart meters).

---

## Entry Point (**init**.py)

The `__init__.py` file is the entry point for your integration.

### Async Setup Entry (Recommended)

```python
"""The Wiener Netze Smart Meter integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import WienerNetzeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# List of platforms to set up
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wiener Netze from a config entry."""

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator
    coordinator = WienerNetzeDataUpdateCoordinator(hass, entry)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
```

### Key Functions

#### `async_setup_entry(hass, entry)`

Called when a config entry is loaded:

1. Initialize your coordinator/API client
2. Store it in `hass.data[DOMAIN][entry.entry_id]`
3. Forward setup to platforms
4. Return `True` for success, `False` for failure

#### `async_unload_entry(hass, entry)`

Called when integration is removed:

1. Unload all platforms
2. Clean up resources
3. Remove data from `hass.data`

### Legacy Setup (YAML-based)

```python
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from configuration.yaml."""
    # Only needed if supporting YAML configuration
    return True
```

---

## Config Flow

Config flow provides UI-based configuration. It's the recommended way for users to set up integrations.

### Basic Config Flow Structure

```python
"""Config flow for Wiener Netze Smart Meter integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WienerNetzeApiClient, WienerNetzeAuthError
from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_API_KEY,
)

_LOGGER = logging.getLogger(__name__)


class WienerNetzeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wiener Netze."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate user input
            try:
                # Test API connection
                session = async_get_clientsession(self.hass)
                client = WienerNetzeApiClient(
                    session=session,
                    client_id=user_input[CONF_CLIENT_ID],
                    client_secret=user_input[CONF_CLIENT_SECRET],
                    api_key=user_input[CONF_API_KEY],
                )

                # Try to authenticate
                await client.authenticate()

                # Create entry
                return self.async_create_entry(
                    title="Wiener Netze Smart Meter",
                    data=user_input,
                )

            except WienerNetzeAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Show form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )
```

### Key Methods

#### `async_step_user(user_input)`

First step shown to user:

- `user_input` is `None` on first call (show form)
- `user_input` contains form data on submission
- Return `async_show_form()` to display form
- Return `async_create_entry()` to create config entry

#### `async_show_form(step_id, data_schema, errors)`

Display a form:

- `step_id`: Identifier for this step
- `data_schema`: Voluptuous schema defining fields
- `errors`: Dict of field errors to display

#### `async_create_entry(title, data)`

Create config entry:

- `title`: Display name in UI
- `data`: Configuration data to store

### Multi-Step Flows

```python
async def async_step_user(self, user_input):
    """Step 1: Credentials."""
    if user_input is not None:
        # Store credentials temporarily
        self.data = user_input
        # Move to next step
        return await self.async_step_meters()

    return self.async_show_form(step_id="user", ...)

async def async_step_meters(self, user_input):
    """Step 2: Select meters."""
    if user_input is not None:
        # Combine with previous data
        self.data.update(user_input)
        return self.async_create_entry(title="...", data=self.data)

    # Fetch available meters using stored credentials
    meters = await self._fetch_meters()

    return self.async_show_form(
        step_id="meters",
        data_schema=vol.Schema({
            vol.Required("meters"): cv.multi_select(meters)
        }),
    )
```

### Error Handling

Define errors in `strings.json`:

```json
{
  "config": {
    "error": {
      "invalid_auth": "Invalid authentication credentials",
      "cannot_connect": "Failed to connect to API",
      "unknown": "Unexpected error occurred"
    }
  }
}
```

---

## Data Update Coordinator

The `DataUpdateCoordinator` coordinates data updates for all entities.

### Why Use a Coordinator?

- **Efficiency**: Single API call for all entities
- **Coordination**: All entities update together
- **Error handling**: Centralized error management
- **Rate limiting**: Prevents excessive API calls

### Basic Coordinator Implementation

```python
"""Data update coordinator for Wiener Netze."""
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WienerNetzeApiClient, WienerNetzeApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WienerNetzeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.api = WienerNetzeApiClient(
            session=async_get_clientsession(hass),
            client_id=entry.data["client_id"],
            client_secret=entry.data["client_secret"],
            api_key=entry.data["api_key"],
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Fetch meter points
            meters = await self.api.get_meter_points()

            # Fetch consumption data for each meter
            data = {}
            for meter in meters:
                meter_id = meter["zaehlpunktnummer"]
                consumption = await self.api.get_consumption(meter_id)
                data[meter_id] = {
                    "meter": meter,
                    "consumption": consumption,
                }

            return data

        except WienerNetzeApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
```

### Using the Coordinator in Entities

```python
class WienerNetzeSensor(CoordinatorEntity):
    """Base sensor entity."""

    def __init__(self, coordinator, meter_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._meter_id = meter_id

    @property
    def native_value(self):
        """Return the sensor value."""
        return self.coordinator.data[self._meter_id]["consumption"]["messwert"]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._meter_id in self.coordinator.data
        )
```

---

## Sensor Platform

The sensor platform creates sensor entities.

### Basic Sensor Implementation

```python
"""Sensor platform for Wiener Netze."""
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WienerNetzeDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: WienerNetzeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensors for each meter
    entities = []
    for meter_id in coordinator.data:
        entities.append(WienerNetzeConsumptionSensor(coordinator, meter_id))

    async_add_entities(entities)


class WienerNetzeConsumptionSensor(CoordinatorEntity, SensorEntity):
    """Sensor for energy consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR

    def __init__(self, coordinator, meter_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._meter_id = meter_id
        self._attr_unique_id = f"{meter_id}_consumption"
        self._attr_name = f"Meter {meter_id} Consumption"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.coordinator.data[self._meter_id]
        return data["consumption"]["messwert"]

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        data = self.coordinator.data[self._meter_id]
        return {
            "quality": data["consumption"]["qualitaet"],
            "time_from": data["consumption"]["zeitVon"],
            "time_to": data["consumption"]["zeitBis"],
            "obis_code": data["consumption"]["obisCode"],
        }

    @property
    def device_info(self):
        """Return device information."""
        meter = self.coordinator.data[self._meter_id]["meter"]
        return {
            "identifiers": {(DOMAIN, self._meter_id)},
            "name": f"Smart Meter {self._meter_id}",
            "manufacturer": "Wiener Netze",
            "model": "Smart Meter",
            "sw_version": meter.get("geraet", {}).get("geraetenummer"),
        }
```

### Entity Properties

Key properties to implement:

- `unique_id` - Unique identifier (required)
- `name` - Display name
- `native_value` or `state` - Current value
- `native_unit_of_measurement` - Unit (e.g., kWh)
- `device_class` - Type of sensor (energy, power, etc.)
- `state_class` - How state behaves (measurement, total, etc.)
- `extra_state_attributes` - Additional data
- `device_info` - Device registry information
- `available` - Whether entity is available

---

## Translations

Translations provide localized strings for the UI.

### strings.json (English)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Set up Wiener Netze Smart Meter",
        "description": "Enter your API credentials",
        "data": {
          "client_id": "Client ID",
          "client_secret": "Client Secret",
          "api_key": "API Key"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid authentication credentials",
      "cannot_connect": "Failed to connect to API",
      "unknown": "Unexpected error occurred"
    },
    "abort": {
      "already_configured": "Integration already configured"
    }
  }
}
```

### translations/de.json (German)

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter einrichten",
        "description": "Geben Sie Ihre API-Zugangsdaten ein",
        "data": {
          "client_id": "Client-ID",
          "client_secret": "Client-Secret",
          "api_key": "API-Schlüssel"
        }
      }
    },
    "error": {
      "invalid_auth": "Ungültige Anmeldedaten",
      "cannot_connect": "Verbindung zur API fehlgeschlagen",
      "unknown": "Unerwarteter Fehler aufgetreten"
    },
    "abort": {
      "already_configured": "Integration bereits konfiguriert"
    }
  }
}
```

### Translation Keys

- Use ISO 639-2 language codes (e.g., `en`, `de`, `fr`)
- Copy `strings.json` structure
- Translate only values, not keys
- Keep placeholders intact

---

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_init.py             # Test __init__.py
├── test_config_flow.py      # Test config flow
├── test_coordinator.py      # Test coordinator
└── test_sensor.py           # Test sensors
```

### Testing Config Flow

```python
"""Test config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY

from custom_components.wiener_netze.const import DOMAIN, CONF_CLIENT_ID


async def test_flow_user_init(hass):
    """Test user step initiates flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


@patch("custom_components.wiener_netze.config_flow.WienerNetzeApiClient")
async def test_flow_user_create_entry(mock_client, hass):
    """Test config entry created."""
    mock_client.return_value.authenticate.return_value = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_CLIENT_ID: "test_id",
            "client_secret": "test_secret",
            CONF_API_KEY: "test_key",
        },
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Wiener Netze Smart Meter"
```

### Required Test Library

```bash
pip install pytest-homeassistant-custom-component
```

This provides fixtures like `hass` for testing.

---

## HACS Compatibility

HACS (Home Assistant Community Store) is the standard way to distribute custom integrations.

### HACS Requirements

1. **Repository Structure**

```
repository_root/
├── custom_components/
│   └── wiener_netze/
│       ├── __init__.py
│       ├── manifest.json
│       └── ...
├── README.md
├── hacs.json
└── LICENSE
```

2. **hacs.json**

```json
{
  "name": "Wiener Netze Smart Meter",
  "render_readme": true,
  "domains": ["sensor"],
  "iot_class": "cloud_polling",
  "homeassistant": "2024.1.0"
}
```

3. **manifest.json Requirements**

Must include:

- `domain`
- `name`
- `version` (semantic versioning)
- `documentation`
- `issue_tracker`
- `codeowners`

4. **GitHub Releases**

- Tag releases with semantic versions (e.g., `v1.0.0`)
- HACS shows latest 5 releases
- Users can choose version to install

### HACS Submission

1. Ensure repository meets requirements
2. Add integration to Home Assistant Brands
3. Submit to HACS via GitHub discussions

---

## Best Practices

### 1. Async/Await

Always use async for I/O operations:

```python
# ✅ Good
async def async_update(self):
    data = await self.api.get_data()

# ❌ Bad
def update(self):
    data = self.api.get_data()  # Blocks event loop
```

### 2. Error Handling

Handle errors gracefully:

```python
try:
    data = await self.api.get_data()
except ApiError as err:
    _LOGGER.error("Failed to fetch data: %s", err)
    raise UpdateFailed(err) from err
```

### 3. Type Hints

Use type hints throughout:

```python
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry
) -> bool:
    """Set up from config entry."""
```

### 4. Logging

Use appropriate log levels:

```python
_LOGGER.debug("Fetching data for meter %s", meter_id)
_LOGGER.info("Successfully authenticated")
_LOGGER.warning("Rate limit approaching")
_LOGGER.error("Failed to connect: %s", error)
```

### 5. Constants

Define constants in `const.py`:

```python
"""Constants for Wiener Netze integration."""

DOMAIN = "wiener_netze"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_KEY = "api_key"
DEFAULT_UPDATE_INTERVAL = 15
```

### 6. Unique IDs

Always provide unique IDs for entities:

```python
self._attr_unique_id = f"{meter_id}_consumption"
```

### 7. Device Registry

Group related entities under devices:

```python
@property
def device_info(self):
    """Return device information."""
    return {
        "identifiers": {(DOMAIN, self._meter_id)},
        "name": f"Smart Meter {self._meter_id}",
        "manufacturer": "Wiener Netze",
        "model": "Smart Meter",
    }
```

### 8. Rate Limiting

Respect API rate limits:

```python
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientTimeout

session = async_get_clientsession(hass)
timeout = ClientTimeout(total=30)
```

### 9. Configuration Validation

Validate user input in config flow:

```python
vol.Schema({
    vol.Required(CONF_CLIENT_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional("update_interval", default=15): cv.positive_int,
})
```

### 10. Testing

Write comprehensive tests:

- Config flow tests
- Coordinator tests
- Entity tests
- Integration tests
- Mock external API calls

---

## Resources

### Official Documentation

- **Home Assistant Developer Docs**: <https://developers.home-assistant.io/>
  - [Creating Integration](https://developers.home-assistant.io/docs/creating_component_index/)
  - [Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
  - [Entity](https://developers.home-assistant.io/docs/core/entity/)
  - [Sensor Platform](https://developers.home-assistant.io/docs/core/entity/sensor/)
  - [Data Update Coordinator](https://developers.home-assistant.io/docs/integration_fetching_data/)

### HACS Documentation

- **HACS**: <https://hacs.xyz/>
  - [Integration Requirements](https://hacs.xyz/docs/publish/integration/)

### Example Integrations

- **Blueprint**: <https://github.com/custom-components/blueprint> (official template)
- **Integration Examples**: <https://github.com/home-assistant/example-custom-config/tree/master/custom_components>

### Tutorial Series

- **Building a Custom Component** by Aaron Godfrey:
  - [Part 1: Structure](https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/)
  - [Part 2: Unit Testing](https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_2/)
  - [Part 3: Config Flow](https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_3/)

### Tools

- **Cookiecutter Template**: <https://github.com/oncleben31/cookiecutter-homeassistant-custom-component>
- **pytest-homeassistant-custom-component**: <https://github.com/MatthewFlamm/pytest-homeassistant-custom-component>
- **Home Assistant Core**: <https://github.com/home-assistant/core> (reference implementations)

### Community

- **Home Assistant Community**: <https://community.home-assistant.io/c/development/14>
- **Discord**: <https://discord.gg/home-assistant> (#devs channel)

---

## Quick Reference

### Essential Imports

```python
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
```

### Minimal Integration Checklist

- [ ] Create `custom_components/<domain>/` directory
- [ ] Add `manifest.json` with all required fields
- [ ] Implement `__init__.py` with `async_setup_entry()`
- [ ] Create `config_flow.py` for UI setup
- [ ] Implement platform (e.g., `sensor.py`)
- [ ] Add `strings.json` with UI strings
- [ ] Add translations in `translations/` folder
- [ ] Write tests in `tests/` directory
- [ ] Create `README.md` with setup instructions
- [ ] Add `hacs.json` for HACS compatibility
- [ ] Tag release with semantic version

---

**This document provides a comprehensive foundation for developing the Wiener Netze Smart Meter Home Assistant integration. Refer to the official Home Assistant developer documentation for the most up-to-date information.**
