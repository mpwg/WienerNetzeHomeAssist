# Task 13: Strings and Translations Setup

**Category:** Home Assistant Integration Core
**Priority:** Medium
**Estimated Effort:** 1-2 hours
**Status:** Not Started

## Description

Create the base strings.json and translation files for the Wiener Netze integration to support internationalization (i18n) in Home Assistant.

## Prerequisites

- **Task 11** completed (Config Flow Implementation)
- Understanding of Home Assistant translation system

## Objectives

1. Create base `strings.json` with all translatable strings
2. Create English translations (`en.json`)
3. Create German translations (`de.json`)
4. Ensure all config flow steps are translated
5. Add entity translations for sensors

## Deliverables

- [ ] Complete `strings.json` file
- [ ] English translations (`translations/en.json`)
- [ ] German translations (`translations/de.json`)
- [ ] Consistent translation keys across all files

## Implementation

### 1. Create strings.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter Setup",
        "description": "Enter your API credentials from the WSTW API Portal. [Get API credentials](https://test-api.wienerstadwerke.at/portal/)",
        "data": {
          "client_id": "OAuth2 Client ID",
          "client_secret": "OAuth2 Client Secret",
          "api_key": "API Gateway Key"
        },
        "data_description": {
          "client_id": "Your OAuth2 Client ID from WSTW API Portal",
          "client_secret": "Your OAuth2 Client Secret (keep confidential)",
          "api_key": "Your x-Gateway-APIKey from the API application"
        }
      },
      "meter_point": {
        "title": "Select Meter Point",
        "description": "Select the smart meter (Zählpunkt) you want to monitor",
        "data": {
          "meter_point": "Meter Point"
        },
        "data_description": {
          "meter_point": "Choose one of your available smart meters"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid credentials. Please verify your Client ID, Client Secret, and API Key.",
      "cannot_connect": "Unable to connect to Wiener Netze API. Please check your internet connection and try again.",
      "no_meter_points": "No smart meters found for this account. Ensure your account is linked in the Smart Meter Portal.",
      "unknown": "An unexpected error occurred. Please try again or check the logs for details.",
      "timeout": "Request timed out. The API server may be temporarily unavailable."
    },
    "abort": {
      "already_configured": "This meter point is already configured.",
      "reauth_successful": "Re-authentication successful."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Wiener Netze Options",
        "description": "Configure update interval and data granularity",
        "data": {
          "scan_interval": "Update interval (minutes)",
          "granularity": "Data granularity"
        }
      }
    }
  },
  "entity": {
    "sensor": {
      "current_power": {
        "name": "Current power"
      },
      "daily_energy": {
        "name": "Daily energy"
      },
      "meter_reading": {
        "name": "Meter reading"
      },
      "monthly_energy": {
        "name": "Monthly energy"
      },
      "yearly_energy": {
        "name": "Yearly energy"
      }
    }
  },
  "services": {
    "refresh_data": {
      "name": "Refresh data",
      "description": "Manually refresh consumption data from the API"
    }
  }
}
```

### 2. Create translations/en.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter Setup",
        "description": "Enter your API credentials from the WSTW API Portal. [Get API credentials](https://test-api.wienerstadwerke.at/portal/)",
        "data": {
          "client_id": "OAuth2 Client ID",
          "client_secret": "OAuth2 Client Secret",
          "api_key": "API Gateway Key"
        },
        "data_description": {
          "client_id": "Your OAuth2 Client ID from WSTW API Portal",
          "client_secret": "Your OAuth2 Client Secret (keep confidential)",
          "api_key": "Your x-Gateway-APIKey from the API application"
        }
      },
      "meter_point": {
        "title": "Select Meter Point",
        "description": "Select the smart meter (Zählpunkt) you want to monitor",
        "data": {
          "meter_point": "Meter Point"
        },
        "data_description": {
          "meter_point": "Choose one of your available smart meters"
        }
      }
    },
    "error": {
      "invalid_auth": "Invalid credentials. Please verify your Client ID, Client Secret, and API Key.",
      "cannot_connect": "Unable to connect to Wiener Netze API. Please check your internet connection and try again.",
      "no_meter_points": "No smart meters found for this account. Ensure your account is linked in the Smart Meter Portal.",
      "unknown": "An unexpected error occurred. Please try again or check the logs for details.",
      "timeout": "Request timed out. The API server may be temporarily unavailable."
    },
    "abort": {
      "already_configured": "This meter point is already configured.",
      "reauth_successful": "Re-authentication successful."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Wiener Netze Options",
        "description": "Configure update interval and data granularity",
        "data": {
          "scan_interval": "Update interval (minutes)",
          "granularity": "Data granularity"
        }
      }
    }
  },
  "entity": {
    "sensor": {
      "current_power": {
        "name": "Current power"
      },
      "daily_energy": {
        "name": "Daily energy"
      },
      "meter_reading": {
        "name": "Meter reading"
      },
      "monthly_energy": {
        "name": "Monthly energy"
      },
      "yearly_energy": {
        "name": "Yearly energy"
      }
    }
  },
  "services": {
    "refresh_data": {
      "name": "Refresh data",
      "description": "Manually refresh consumption data from the API"
    }
  }
}
```

### 3. Create translations/de.json

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Wiener Netze Smart Meter Einrichtung",
        "description": "Geben Sie Ihre API-Zugangsdaten aus dem WSTW API-Portal ein. [API-Zugangsdaten erhalten](https://test-api.wienerstadwerke.at/portal/)",
        "data": {
          "client_id": "OAuth2 Client-ID",
          "client_secret": "OAuth2 Client-Secret",
          "api_key": "API Gateway Schlüssel"
        },
        "data_description": {
          "client_id": "Ihre OAuth2 Client-ID aus dem WSTW API-Portal",
          "client_secret": "Ihr OAuth2 Client-Secret (vertraulich behandeln)",
          "api_key": "Ihr x-Gateway-APIKey aus der API-Anwendung"
        }
      },
      "meter_point": {
        "title": "Zählpunkt auswählen",
        "description": "Wählen Sie den Smart Meter (Zählpunkt), den Sie überwachen möchten",
        "data": {
          "meter_point": "Zählpunkt"
        },
        "data_description": {
          "meter_point": "Wählen Sie einen Ihrer verfügbaren Smart Meter"
        }
      }
    },
    "error": {
      "invalid_auth": "Ungültige Zugangsdaten. Bitte überprüfen Sie Ihre Client-ID, Client-Secret und API-Key.",
      "cannot_connect": "Verbindung zur Wiener Netze API nicht möglich. Bitte überprüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.",
      "no_meter_points": "Keine Smart Meter für dieses Konto gefunden. Stellen Sie sicher, dass Ihr Konto im Smart Meter Portal verknüpft ist.",
      "unknown": "Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es erneut oder überprüfen Sie die Protokolle.",
      "timeout": "Zeitüberschreitung der Anfrage. Der API-Server ist möglicherweise vorübergehend nicht verfügbar."
    },
    "abort": {
      "already_configured": "Dieser Zählpunkt ist bereits konfiguriert.",
      "reauth_successful": "Erneute Authentifizierung erfolgreich."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "Wiener Netze Optionen",
        "description": "Aktualisierungsintervall und Datengranularität konfigurieren",
        "data": {
          "scan_interval": "Aktualisierungsintervall (Minuten)",
          "granularity": "Datengranularität"
        }
      }
    }
  },
  "entity": {
    "sensor": {
      "current_power": {
        "name": "Aktuelle Leistung"
      },
      "daily_energy": {
        "name": "Tagesverbrauch"
      },
      "meter_reading": {
        "name": "Zählerstand"
      },
      "monthly_energy": {
        "name": "Monatsverbrauch"
      },
      "yearly_energy": {
        "name": "Jahresverbrauch"
      }
    }
  },
  "services": {
    "refresh_data": {
      "name": "Daten aktualisieren",
      "description": "Verbrauchsdaten manuell von der API abrufen"
    }
  }
}
```

### 4. Translation Key Guidelines

**Naming Conventions:**

- Use snake_case for all keys
- Be descriptive but concise
- Group related translations together
- Use consistent terminology across languages

**Translation Structure:**

- `config.step.*` - Configuration flow steps
- `config.error.*` - Error messages
- `config.abort.*` - Abort reasons
- `options.step.*` - Options flow
- `entity.sensor.*` - Sensor entity names
- `services.*` - Service descriptions

### 5. Testing Translations

Create a test to verify translation completeness:

```python
"""Test translations."""
import json
import pathlib


def test_translation_completeness():
    """Verify all translation files have same keys."""
    base_path = pathlib.Path(__file__).parent.parent / "custom_components" / "wiener_netze"

    # Load strings.json
    with open(base_path / "strings.json") as f:
        strings = json.load(f)

    # Load translations
    with open(base_path / "translations" / "en.json") as f:
        en = json.load(f)

    with open(base_path / "translations" / "de.json") as f:
        de = json.load(f)

    # Verify structure matches
    assert en.keys() == strings.keys()
    assert de.keys() == strings.keys()

    # Check config keys
    assert en["config"]["step"].keys() == strings["config"]["step"].keys()
    assert de["config"]["step"].keys() == strings["config"]["step"].keys()


def test_no_missing_translations():
    """Ensure no placeholder strings remain."""
    base_path = pathlib.Path(__file__).parent.parent / "custom_components" / "wiener_netze"

    for lang_file in ["en.json", "de.json"]:
        with open(base_path / "translations" / lang_file) as f:
            content = f.read()

        # Check for common placeholder patterns
        assert "TODO" not in content
        assert "FIXME" not in content
        assert "XXX" not in content
```

## Acceptance Criteria

- [ ] `strings.json` contains all translatable strings
- [ ] English translations complete and correct
- [ ] German translations complete and correct
- [ ] All config flow steps translated
- [ ] All error messages translated
- [ ] All entity names translated
- [ ] Translation structure matches Home Assistant conventions
- [ ] No missing or placeholder translations
- [ ] Translations display correctly in UI

## Testing

```bash
# Verify JSON syntax
python -m json.tool custom_components/wiener_netze/strings.json
python -m json.tool custom_components/wiener_netze/translations/en.json
python -m json.tool custom_components/wiener_netze/translations/de.json

# Run translation tests
pytest tests/test_translations.py -v

# Test in Home Assistant
# 1. Set Home Assistant language to English
# 2. Add integration and verify English strings
# 3. Set Home Assistant language to German
# 4. Verify German strings appear correctly
```

## References

- [Translation Documentation](https://developers.home-assistant.io/docs/internationalization/)
- [Translation Best Practices](https://developers.home-assistant.io/docs/internationalization/core/)
- [Strings.json Schema](https://developers.home-assistant.io/docs/internationalization/core/#stringsjson)

## Notes

- Home Assistant automatically loads the correct translation based on user's language setting
- `strings.json` is the base file - translations inherit from it
- Use translation_key in entities to link to translations
- Keep strings concise but informative
- Provide helpful error messages with troubleshooting hints
- Include links to documentation where helpful
- Test both languages in the UI before release

## Next Task

→ **Task 14:** Device Registry Integration
