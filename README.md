# Wiener Netze Smart Meter - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Home Assistant integration for Wiener Netze Smart Meters, providing real-time energy consumption monitoring.

## Features

- Real-time energy consumption data
- 15-minute interval readings
- Daily and meter reading aggregation
- OAuth2 authentication with Wiener Netze API
- Multiple smart meter support
- Device registry integration

## Installation

### Prerequisites

Before installing this integration, you need:

1. **Wiener Netze Smart Meter** installed and active
2. **API Credentials** from [WSTW API Portal](https://test-api.wienerstadwerke.at/portal/)
3. **HACS** installed in Home Assistant ([HACS Installation Guide](https://hacs.xyz/docs/setup/download))

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mpwg/WienerNetzeHomeAssist`
6. Select category: "Integration"
7. Click "Add"
8. Find "Wiener Netze Smart Meter" in HACS
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/mpwg/WienerNetzeHomeAssist/releases)
2. Extract the `custom_components/wiener_netze` directory
3. Copy it to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

After installation:

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Wiener Netze Smart Meter"**
4. Follow the configuration wizard

For detailed setup instructions, see [SETUP.md](dokumentation/SETUP.md)

## Sensors

The integration provides the following sensors:

- **Current Consumption** - Latest 15-minute reading
- **Daily Consumption** - Daily total consumption
- **Meter Reading** - Current meter reading

## Development

See [HOME_ASSISTANT_PLUGIN_DEVELOPMENT.md](dokumentation/HOME_ASSISTANT_PLUGIN_DEVELOPMENT.md) for development documentation.

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

The Wiener Netze Smart Meter API is licensed under CC BY-NC-ND 4.0.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/mpwg/WienerNetzeHomeAssist/issues).
