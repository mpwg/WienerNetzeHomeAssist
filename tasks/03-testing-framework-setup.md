# Task 03: Testing Framework Setup

**Category:** Project Setup  
**Priority:** High  
**Estimated Effort:** 2-3 hours  
**Status:** Not Started

## Description

Set up the testing framework for the integration using pytest and pytest-homeassistant-custom-component, including fixtures and test configuration.

## Prerequisites

- **Task 01** completed (Development Environment Setup)
- **Task 02** completed (Repository Structure Setup)
- pytest-homeassistant-custom-component installed

## Objectives

1. Configure pytest for Home Assistant testing
2. Create test fixtures
3. Set up mock API responses
4. Create test utilities
5. Write sample test to verify setup

## Deliverables

- [ ] `tests/conftest.py` with fixtures
- [ ] `tests/fixtures/` directory with mock data
- [ ] `tests/test_setup.py` with basic tests
- [ ] pytest configuration in `pyproject.toml`
- [ ] All tests passing

## Steps

### 1. Create Test Fixtures in conftest.py

```python
"""Fixtures for tests."""
import pytest
from unittest.mock import patch, MagicMock
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
        unique_id="test_unique_id",
    )


@pytest.fixture
def mock_api_client():
    """Return a mock API client."""
    with patch(
        "custom_components.wiener_netze.api.WienerNetzeApiClient"
    ) as mock_client:
        client = mock_client.return_value
        client.authenticate.return_value = True
        client.get_meter_points.return_value = [
            {
                "zaehlpunktnummer": "AT0000000000000000000000000000001",
                "geraet": {
                    "geraetenummer": "12345678"
                }
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
async def setup_integration(hass: HomeAssistant, mock_config_entry, mock_api_client):
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
        "geraet": {
            "geraetenummer": "12345678"
        },
        "anlage": {
            "anlagennummer": "AN123456"
        }
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
            }
        ]
    }
```

### 2. Create Test Fixtures Directory

```bash
mkdir -p tests/fixtures
```

### 3. Create Mock API Response Files

**tests/fixtures/oauth_token.json:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "smart-meter-api"
}
```

**tests/fixtures/meter_points.json:**

```json
[
  {
    "zaehlpunktnummer": "AT0000000000000000000000000000001",
    "geraet": {
      "geraetenummer": "12345678"
    },
    "anlage": {
      "anlagennummer": "AN123456"
    }
  }
]
```

**tests/fixtures/consumption_quarter_hour.json:**

```json
{
  "zaehlpunkt": "AT0000000000000000000000000000001",
  "wertetyp": "QUARTER_HOUR",
  "werte": [
    {
      "messwert": 0.25,
      "qualitaet": "VAL",
      "zeitVon": "2025-11-10T00:00:00+01:00",
      "zeitBis": "2025-11-10T00:15:00+01:00",
      "obisCode": "1-1:1.8.0"
    },
    {
      "messwert": 0.3,
      "qualitaet": "VAL",
      "zeitVon": "2025-11-10T00:15:00+01:00",
      "zeitBis": "2025-11-10T00:30:00+01:00",
      "obisCode": "1-1:1.8.0"
    }
  ]
}
```

### 4. Create Test Utilities

**tests/utils.py:**

```python
"""Test utilities."""
import json
from pathlib import Path


def load_fixture(filename: str) -> str:
    """Load a fixture file."""
    path = Path(__file__).parent / "fixtures" / filename
    return path.read_text()


def load_json_fixture(filename: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads(load_fixture(filename))
```

### 5. Create Basic Setup Test

**tests/test_setup.py:**

```python
"""Test integration setup."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState

from custom_components.wiener_netze.const import DOMAIN


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_api_client):
    """Test setting up config entry."""
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data


async def test_unload_entry(hass: HomeAssistant, mock_config_entry, mock_api_client):
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

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR
```

### 6. Update pyproject.toml

Ensure pytest configuration is complete:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

### 7. Create Test Runner Script

**run_tests.sh:**

```bash
#!/bin/bash
set -e

echo "Running tests..."
pytest tests/ -v --cov=custom_components.wiener_netze --cov-report=term-missing

echo "Running linters..."
black --check custom_components/ tests/
flake8 custom_components/ tests/
pylint custom_components/wiener_netze/

echo "Running type checker..."
mypy custom_components/wiener_netze/

echo "All checks passed!"
```

Make executable:

```bash
chmod +x run_tests.sh
```

## Acceptance Criteria

- [ ] conftest.py contains all required fixtures
- [ ] Mock JSON files created in tests/fixtures/
- [ ] Test utilities module created
- [ ] Basic setup tests written and passing
- [ ] pytest configuration complete
- [ ] Test runner script works
- [ ] Coverage report generates successfully

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_setup.py -v

# Run with coverage
pytest tests/ --cov=custom_components.wiener_netze --cov-report=html

# Check coverage report
open htmlcov/index.html

# Run tests with output
pytest tests/ -v -s
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing)

## Notes

- Use `async` fixtures for Home Assistant components
- Mock external API calls to avoid network dependencies
- Keep mock data realistic based on actual API responses
- Use `autouse=True` for fixtures that should always run
- Coverage target: >80% for production code

## Next Task

→ **Task 04:** HACS Configuration Setup
