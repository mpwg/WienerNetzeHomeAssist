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

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Wiener Netze Smart Meter"
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/wiener_netze` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ ADD INTEGRATION"
3. Search for "Wiener Netze Smart Meter"
4. Follow the configuration steps

## Setup Requirements

- Wiener Netze Smart Meter account
- API credentials from WSTW API Portal
- Active smart meter (Zählpunkt)

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
