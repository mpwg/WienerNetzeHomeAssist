# Wiener Netze Smart Meter Home Assistant Integration - Implementation Plan

## Executive Summary

This document outlines the implementation plan for a Home Assistant custom integration that connects Wiener Netze Smart Meters to Home Assistant, providing real-time and historical energy consumption data.

**Project Goals:**

- Enable Home Assistant users to monitor their Wiener Netze smart meter data
- Provide accurate energy consumption information in real-time
- Support multiple metering points (Zählpunkte)
- Implement secure OAuth2 authentication
- Follow Home Assistant best practices and guidelines

**Target Completion:** 6-8 weeks (depending on development resources)

---

## Table of Contents

1. [Project Scope](#project-scope)
2. [Technical Architecture](#technical-architecture)
3. [Implementation Phases](#implementation-phases)
4. [API Analysis](#api-analysis)
5. [Component Structure](#component-structure)
6. [Development Roadmap](#development-roadmap)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)
9. [Maintenance & Support](#maintenance--support)

---

## Project Scope

### Prerequisites

**API Access Requirements:**

Before using this integration, users must complete the following steps to obtain API credentials:

#### 1. Register at WSTW API Portal

- **Portal URL**: https://test-api.wienerstadwerke.at/portal/
- Click the **"Sign In"** button on the portal homepage
- Fill in your personal information
- Review and accept the terms of use
- Follow password security guidelines
- Confirm your email address via the confirmation link sent to you
- After login, you'll see the dashboard with three main sections:
  - **API-Katalog**: Overview of all WSTW API collections
  - **API Ausprobieren**: Manage your API applications
  - **API-Einblicke**: Statistics and analytics for API usage

#### 2. Create API Application

Three ways to create an application:

- Through "API ausprobieren" (Try API)
- Through "API-Katalog" → Select WN Smart Meter API → Click "Anwenden"
- Through Profile dropdown → "Anwendungen verwalten"

When creating:

- Select Phase (Environment): **PROD**
- Select API Collection: **WN Smart Meter API**
- Provide Application Name and Description
- Callback URL is automatically assigned to: `https://test-api.wienerstadwerke.at/portal/rest/v1/oauth/callback`

After successful creation (status changes from INAKTIV to LIVE), you'll receive an email with:

- **API Key** (x-Gateway-APIKey): e.g., `d4ba6184-ca88-4246-a182-14da305d1520`
- **Client ID**: Individually provided
- **Client Secret**: Individually provided
- **⚠️ Keep these credentials confidential!**

#### 3. Register in Smart Meter Webportal

- Create an account at the Smart Meter Webportal
- Ensure you have active metering points with available data
- This is required to link your API application with your metering data

#### 4. Link API Application with Smart Meter Webportal

Prerequisites for linking:

1. Successfully registered in WSTW API Portal
2. Created an API application (or have access to one)
3. Registered in Smart Meter Webportal with available data

**Linking Process**:

- Send email to `support.sm-portal@wienit.at`
- Email template available in portal under "API-Dokumentation"
- Include:
  - Your API application name
  - Your Smart Meter Webportal email address
- Support team will create unique Client-ID and Client-Secret linked to your account
- After setup, view your credentials in Smart Meter Business Portal:
  - Navigate to: **Anlagendaten** → **Vertragsverbindung hinzufügen/entfernen** → **API**

**Note**: Multiple Smart Meter Webportal profiles can be linked to one API application.

**The integration will provide clear setup instructions and links to guide users through this process.**

### In Scope

✅ **Core Features:**

- OAuth2 client credentials authentication with Wiener Netze API
- Dual authentication (OAuth2 Bearer token + API Key header)
- Automatic discovery and setup of available metering points
- Real-time energy consumption sensors
- Historical data retrieval (15-minute, hourly, daily, monthly, yearly intervals)
- Device information display (meter number, equipment number, address)
- Support for multiple metering points per account
- Configurable update intervals
- Proper error handling and logging

✅ **User Experience:**

- Config flow for easy setup
- Clear error messages
- Automatic token refresh
- Sensor attributes with detailed metadata
- Integration with Home Assistant Energy Dashboard

✅ **Technical Requirements:**

- Async/await implementation
- Type hints throughout
- Comprehensive test coverage
- Documentation (user and developer)
- HACS compatibility

### Out of Scope (Future Enhancements)

❌ **Phase 2 Features:**

- Tariff information and cost calculations
- Comparison with previous periods
- Anomaly detection
- Export functionality
- Push notifications for unusual consumption

---

## Technical Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Wiener Netze Integration                    │    │
│  │                                                     │    │
│  │  ┌──────────────┐      ┌────────────────────────┐   │    │
│  │  │ Config Flow  │      │   Data Coordinator     │   │    │
│  │  │  (OAuth2)    │      │  (Update Handler)      │   │    │
│  │  └──────────────┘      └────────────────────────┘   │    │
│  │         │                        │                  │.   │
│  │         │                        │                  │    │
│  │  ┌──────▼────────────────────────▼──────────────┐   │    │
│  │  │           API Client Library                 │   │    │
│  │  │  (Authentication, Rate Limiting, Caching)    │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │         │                                           │.   │
│  └─────────┼───────────────────────────────────────────┘    │
│            │                                                │
│  ┌─────────▼──────────────────────────────────────────┐     │
│  │              Sensor Entities                       │     │
│  │  • Current Consumption  • Daily Total              │     │
│  │  • Meter Reading       • Historical Data           │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS / OAuth2
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Wiener Netze Smart Meter API                   │
│      https://api.wstw.at/gateway/WN_SMART_METER_API/1.0     │
│                                                             │
│  • /zaehlpunkte              (List metering points)         │
│  • /zaehlpunkte/{id}         (Get specific meter)           │
│  • /zaehlpunkte/messwerte    (Get consumption data)         │
│  • /zaehlpunkte/{id}/messwerte (Get meter-specific data)    │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Core:**

- Python 3.11+
- Home Assistant Core 2024.1+
- aiohttp for async HTTP requests
- OAuth2 for authentication

**Testing:**

- pytest
- pytest-homeassistant-custom-component
- pytest-aiohttp
- pytest-cov for coverage

**Development:**

- black for code formatting
- pylint for linting
- mypy for type checking
- pre-commit hooks

---

## API Analysis

### Available Endpoints

#### 1. List All Metering Points

**Endpoint:** `GET /zaehlpunkte`
**Parameters:**

- `resultType` (optional) - Values: `ALL` or `SMARTMETER`
- `zaehlpunkt` (optional, repeatable) - Filter by specific meter(s)
- `webProfileId` (optional)

**Headers:**

- `Authorization: Bearer {access_token}`
- `x-Gateway-APIKey: {api_key}`
- `Accept: application/json`

**Use Case:** Initial setup to discover available meters

#### 2. Get Specific Metering Point

**Endpoint:** `GET /zaehlpunkte/{zaehlpunkt}`
**Parameters:**

- `zaehlpunkt` (path) - Meter ID
- `webProfileId` (optional)

**Response Includes:**

- Anlage (Installation) data
- Gerät (Device) information
- Verbrauchsstelle (Consumption location/address)
- IDEX data (customer interface, granularity)

**Use Case:** Device information display

#### 3. Get Consumption Data (All Meters)

**Endpoint:** `GET /zaehlpunkte/messwerte`
**Required Parameters:**

- `datumVon` - Start date (format: "YYYY-MM-DD")
- `datumBis` - End date (format: "YYYY-MM-DD")
- `wertetyp` - Value type: "QUARTER_HOUR", "DAY", or "METER_READ"

**Optional Parameters:**

- `zaehlpunkt` - Filter by specific meter
- `resultType` - "SMART_METER" or "ALL" (includes Ferraris meters)

**Use Case:** Batch retrieval for multiple meters

**Note:** Per PDF documentation, wertetyp controls granularity:

- "QUARTER_HOUR": 15-minute interval data
- "DAY": Daily consumption values
- "METER_READ": Actual meter readings (Zählerstand)

#### 4. Get Consumption Data (Specific Meter)

**Endpoint:** `GET /zaehlpunkte/{zaehlpunkt}/messwerte`
**Required Parameters:**

- `zaehlpunkt` (path) - Meter ID
- `datumVon` - Start date (format: "YYYY-MM-DD")
- `datumBis` - End date (format: "YYYY-MM-DD")
- `wertetyp` - Value type: "QUARTER_HOUR", "DAY", or "METER_READ"

**Response Structure:**

```json
{
  "zaehlpunkt": "string",
  "zaehlwerke": [
    {
      "obisCode": "string",
      "einheit": "string",
      "messwerte": [
        {
          "zeitVon": "string",
          "zeitBis": "string",
          "messwert": 0,
          "qualitaet": "string"
        }
      ]
    }
  ]
}
```

**Use Case:** Regular sensor updates

**Quality Indicators (`qualitaet` field):**

- `VAL` - Validated actual value (tatsächlicher Wert)
- `EST` - Estimated/calculated value (geschätzter/berechneter Wert)

### Data Types (wertetyp)

Per API documentation, the following values are supported:

- `QUARTER_HOUR` - 15-minute intervals (most granular)
- `DAY` - Daily totals
- `METER_READ` - Actual meter readings (Zählerstand)

Note: The PDF documentation specifies these exact values. The OpenAPI spec may show different values (15MIN, HOUR, MONTH, YEAR) but the actual API accepts QUARTER_HOUR, DAY, and METER_READ.

### Authentication

**Type:** OAuth2 with API Key
**Security Schemes:**

- `x-Gateway-APIKey` - API Key in header (required for all requests)
- `OAuth2` - Client credentials flow with Bearer token

**OAuth2 Details:**

- **Token URL:** `https://log.wien/auth/realms/logwien/protocol/openid-connect/token`
- **Grant Type:** `client_credentials`
- **Token Type:** Bearer
- **Content-Type:** `application/x-www-form-urlencoded`

**Requirements:**

- Client ID and Client Secret (obtained from Wiener Netze)
- API Key (separate from OAuth2 credentials)
- Token refresh mechanism
- Secure storage of credentials and tokens in Home Assistant
- Both OAuth2 Bearer token AND API key must be included in all API requests

**Registration Process:**

Users must request API access by emailing `support.sm-portal@wienit.at` with:

- Application name from WSTW Developer Portal
- Smart Meter Portal email address

---

## Component Structure

### Directory Structure

```
custom_components/
└── wiener_netze/
    ├── __init__.py              # Component setup and integration
    ├── manifest.json            # Integration metadata
    ├── config_flow.py           # Configuration UI flow
    ├── const.py                 # Constants and configuration
    ├── sensor.py                # Sensor platform implementation
    ├── coordinator.py           # Data update coordinator
    ├── api.py                   # API client library
    ├── oauth2.py                # OAuth2 implementation
    ├── strings.json             # Translatable strings
    ├── translations/
    │   ├── en.json              # English translations
    │   └── de.json              # German translations
    ├── icons.json               # Custom icons (optional)
    └── services.yaml            # Service definitions (if needed)

tests/
├── __init__.py
├── conftest.py                  # Test fixtures
├── test_init.py                 # Integration tests
├── test_config_flow.py          # Config flow tests
├── test_sensor.py               # Sensor tests
├── test_coordinator.py          # Coordinator tests
├── test_api.py                  # API client tests
└── fixtures/
    ├── api_responses.json       # Mock API responses
    └── test_data.py             # Test data helpers

dokumentation/
├── Export_WN_SMART_METER_API.yaml  # API specification
├── README.md                    # User documentation
├── SETUP.md                     # Setup guide
└── DEVELOPMENT.md               # Developer guide
```

### File Descriptions

#### `manifest.json`

Defines integration metadata, dependencies, and configuration.

```json
{
  "domain": "wiener_netze",
  "name": "Wiener Netze Smart Meter",
  "codeowners": ["@mpwg"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/mpwg/WienerNetzeHomeAssist",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/mpwg/WienerNetzeHomeAssist/issues",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0"
}
```

#### `const.py`

Central location for all constants.

```python
DOMAIN = "wiener_netze"
CONF_METER_POINTS = "meter_points"
CONF_API_KEY = "api_key"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
DEFAULT_UPDATE_INTERVAL = 15  # minutes

# API Endpoints
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://log.wien/auth/realms/logwien/protocol/openid-connect/token"
OAUTH_GRANT_TYPE = "client_credentials"

# Portal URLs (for user documentation)
API_PORTAL_URL = "https://test-api.wienerstadwerke.at/portal/"
API_PORTAL_CALLBACK = "https://test-api.wienerstadwerke.at/portal/rest/v1/oauth/callback"

# Data granularity options (wertetyp parameter)
GRANULARITY_QUARTER_HOUR = "QUARTER_HOUR"
GRANULARITY_DAY = "DAY"
GRANULARITY_METER_READ = "METER_READ"

# Result type options
RESULT_TYPE_ALL = "ALL"
RESULT_TYPE_SMART_METER = "SMART_METER"
```

#### `api.py`

API client handling all HTTP communication.

**Key Classes:**

- `WienerNetzeApiClient` - Main API client
- `WienerNetzeAuthError` - Authentication errors
- `WienerNetzeApiError` - General API errors
- `RateLimiter` - Rate limiting handler

**Key Methods:**

- `async def authenticate()` - OAuth2 authentication
- `async def get_meter_points()` - Fetch all meters
- `async def get_meter_info(meter_id)` - Get meter details
- `async def get_consumption_data(meter_id, date_from, date_to, value_type)` - Fetch consumption

#### `coordinator.py`

Data update coordinator following HA patterns.

```python
class WienerNetzeDataUpdateCoordinator(DataUpdateCoordinator):
    """Manages fetching data from API."""

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        # Update all configured meters
        # Handle errors
        # Return processed data
```

#### `sensor.py`

Sensor entities for consumption data.

**Sensor Types:**

- `WienerNetzePowerSensor` - Current power consumption
- `WienerNetzeEnergySensor` - Energy totals (daily, monthly, etc.)
- `WienerNetzeMeterReadingSensor` - Cumulative meter reading

#### `config_flow.py`

User-friendly configuration flow.

**Steps:**

1. User provides Client ID, Client Secret, and API Key
2. System authenticates via OAuth2 client credentials flow
3. Retrieve available metering points (Zählpunkte)
4. User selects which meters to monitor (if multiple available)
5. Configuration confirmation
6. Options for update interval and data granularity

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Objectives:**

- Set up project structure
- Implement basic API client
- Create authentication flow

**Tasks:**

1. Create directory structure and files
2. Set up development environment with test credentials
3. Implement `api.py` with basic HTTP client using aiohttp
4. Implement OAuth2 client credentials flow in `oauth2.py`
   - Token endpoint: `https://log.wien/auth/realms/logwien/protocol/openid-connect/token`
   - Grant type: `client_credentials`
   - Content-Type: `application/x-www-form-urlencoded`
5. Implement dual authentication (OAuth2 + API Key)
   - Add `Authorization: Bearer {token}` header
   - Add `x-Gateway-APIKey: {api_key}` header
6. Create `manifest.json` and `const.py` with correct URLs
7. Implement token caching and refresh logic
8. Write initial unit tests for API client
9. Document API client usage and authentication flow

**Deliverables:**

- ✅ Working API client that can authenticate with both OAuth2 and API Key
- ✅ Ability to fetch metering points with proper headers
- ✅ Token refresh mechanism
- ✅ Comprehensive error handling for all API status codes
- ✅ Unit tests with >80% coverage

**Acceptance Criteria:**

- API client successfully obtains OAuth2 token from log.wien
- All requests include both Bearer token and API Key headers
- Can retrieve list of metering points with resultType parameter
- Token is automatically refreshed when expired
- All HTTP errors are properly caught and handled with descriptive messages
- Tests pass with mocked API responses

**HTTP Status Codes to Handle** (per API documentation):

- `200 OK` - Successful request
- `400 Bad Request` - Incorrect query syntax or missing required parameters
- `403 Forbidden` - User not authorized to access resource
- `404 Not Found` - API resource not found
- `408 Request Timeout` - Request took too long to complete
- `500 Internal Server Error` - Unexpected server error

---

### Phase 2: Config Flow (Week 2-3)

**Objectives:**

- Create user-friendly setup experience
- Handle OAuth2 client credentials flow in Home Assistant
- Allow meter selection

**Tasks:**

1. Implement `config_flow.py` with OAuth2 client credentials flow
2. Create user input form for Client ID, Client Secret, and API Key
3. Implement automatic meter discovery after authentication
4. Implement meter selection interface (multi-select)
5. Add options flow for update interval and data granularity
6. Add validation for credentials during setup
7. Create translations (`strings.json`, `en.json`, `de.json`)
8. Include setup instructions for obtaining API credentials
9. Write config flow tests
10. Test with actual Home Assistant instance

**Deliverables:**

- ✅ Complete config flow
- ✅ OAuth2 authentication working in HA
- ✅ Meter selection UI
- ✅ Translations (EN/DE)

**Acceptance Criteria:**

- User can complete setup through UI
- OAuth2 tokens are securely stored
- Multiple meters can be selected
- Config flow handles errors gracefully
- Tests pass

---

### Phase 3: Data Coordinator (Week 3-4)

**Objectives:**

- Implement data fetching logic
- Create update coordinator
- Handle data transformation

**Tasks:**

1. Implement `coordinator.py` with DataUpdateCoordinator
2. Create data fetching methods for all meter types
3. Implement caching to reduce API calls
4. Add retry logic for failed requests
5. Transform API data to HA-friendly format
6. Handle token refresh
7. Write coordinator tests

**Deliverables:**

- ✅ Working data coordinator
- ✅ Automatic updates at configured interval
- ✅ Token refresh mechanism
- ✅ Data caching

**Acceptance Criteria:**

- Coordinator fetches data on schedule
- Failed requests are retried appropriately
- Token refresh works automatically
- Data is properly cached
- Tests pass

---

### Phase 4: Sensor Implementation (Week 4-5)

**Objectives:**

- Create sensor entities
- Display consumption data
- Integrate with Energy Dashboard

**Tasks:**

1. Implement base sensor class
2. Create power consumption sensor (W)
3. Create energy consumption sensors (kWh) for different periods
4. Add meter reading sensor
5. Implement sensor attributes (quality, timestamps, device info)
6. Configure device information
7. Add Energy Dashboard compatibility
8. Write sensor tests

**Deliverables:**

- ✅ Multiple sensor types
- ✅ Device information displayed
- ✅ Energy Dashboard integration
- ✅ Proper units and device classes

**Acceptance Criteria:**

- Sensors update with fresh data
- Energy Dashboard recognizes sensors
- Device information is complete
- Sensor attributes provide useful metadata
- Tests pass

---

### Phase 5: Testing & Refinement (Week 5-6)

**Objectives:**

- Comprehensive testing
- Bug fixes
- Performance optimization

**Tasks:**

1. Complete integration tests
2. Test with multiple meter configurations
3. Test error scenarios (network issues, API errors, invalid tokens)
4. Performance testing and optimization
5. Memory leak testing
6. Load testing (API rate limits)
7. Documentation review
8. Code review and refactoring

**Deliverables:**

- ✅ Complete test suite (>90% coverage)
- ✅ Performance benchmarks
- ✅ Bug fixes
- ✅ Optimized code

**Acceptance Criteria:**

- All tests pass
- No memory leaks
- API rate limits respected
- Code follows HA best practices
- Documentation is complete

---

### Phase 6: Documentation & Release (Week 6-7)

**Objectives:**

- Complete documentation
- Prepare for release
- HACS compatibility

**Tasks:**

1. Write user README with setup instructions
2. Create SETUP.md with detailed configuration guide
3. Write DEVELOPMENT.md for contributors
4. Document all configuration options
5. Create example configurations
6. Add screenshots/GIFs of setup process
7. Prepare HACS submission
8. Create release notes
9. Set up GitHub Actions for CI/CD

**Deliverables:**

- ✅ Complete documentation
- ✅ HACS-compatible repository
- ✅ CI/CD pipeline
- ✅ Release v1.0.0

**Acceptance Criteria:**

- Documentation is clear and comprehensive
- HACS validation passes
- CI/CD pipeline runs successfully
- Release is tagged and published

---

### Phase 7: Community Release (Week 7-8)

**Objectives:**

- Publish to HACS
- Community support
- Initial bug fixes

**Tasks:**

1. Submit to HACS default repository
2. Post on Home Assistant community forum
3. Monitor GitHub issues
4. Respond to user questions
5. Fix reported bugs
6. Gather feedback for v2.0

**Deliverables:**

- ✅ HACS listing
- ✅ Community awareness
- ✅ Bug fix releases (v1.0.x)

**Acceptance Criteria:**

- Integration is available in HACS
- Community feedback is positive
- Critical bugs are fixed within 48 hours
- Documentation is updated based on user feedback

---

## Development Roadmap

### Milestone 1: MVP (End of Phase 4)

- Basic integration working
- Single meter support
- Daily consumption data
- Manual configuration acceptable

### Milestone 2: v1.0 Release (End of Phase 6)

- Complete config flow
- Multiple meter support
- All data granularities
- HACS compatible
- Full documentation

### Milestone 3: v1.1 Enhancement (Post-release)

- Community feedback incorporated
- Performance improvements
- Additional sensors (if requested)
- Bug fixes

### Future Versions (v2.0+)

- Cost calculations
- Tariff integration
- Anomaly detection
- Historical data visualization
- Export functionality

---

## Testing Strategy

### Unit Tests

**Coverage Target:** >90%

**Test Files:**

- `test_api.py` - API client methods
- `test_oauth2.py` - Authentication flow
- `test_coordinator.py` - Data coordinator logic
- `test_sensor.py` - Sensor entities
- `test_config_flow.py` - Configuration flow

**Mocking Strategy:**

- Mock all HTTP requests using `aiohttp` test utilities
- Create fixtures for API responses from OpenAPI spec
- Mock OAuth2 token exchange
- Mock Home Assistant core functionality

### Integration Tests

**Scope:**

- End-to-end flow from config to sensor update
- Multiple meter configurations
- Token refresh scenarios
- Error recovery

**Test Environment:**

- pytest-homeassistant-custom-component
- Mock Home Assistant instance
- Simulated API responses

### Manual Testing

**Test Cases:**

1. Fresh installation and setup
2. Multiple meter configuration
3. Network interruption during update
4. API rate limit handling
5. Token expiration and refresh
6. Energy Dashboard integration
7. Sensor entity customization

**Test Devices:**

- Home Assistant Core (container)
- Home Assistant OS (VM)
- Home Assistant Supervised

---

## Deployment Plan

### Pre-Release Checklist

- [ ] All tests passing
- [ ] Code linted and formatted
- [ ] Documentation complete
- [ ] CHANGELOG.md updated
- [ ] Version number updated
- [ ] GitHub Actions CI passing
- [ ] HACS validation passing
- [ ] Manual testing completed

### Release Process

1. **Create Release Branch**

   ```bash
   git checkout -b release/v1.0.0
   ```

2. **Final Testing**

   - Run full test suite
   - Manual testing on HA instance
   - Test HACS installation

3. **Update Documentation**

   - Finalize README
   - Update version numbers
   - Create release notes

4. **Tag Release**

   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

5. **GitHub Release**

   - Create GitHub release with tag
   - Attach release notes
   - Include installation instructions

6. **HACS Submission**
   - Fork HACS default repository
   - Add integration to default.json
   - Create pull request

### Post-Release

- Monitor GitHub issues
- Respond to community feedback
- Plan bug fix releases
- Start planning v1.1 features

---

## Maintenance & Support

### Ongoing Tasks

**Weekly:**

- Monitor GitHub issues
- Respond to user questions
- Review pull requests

**Monthly:**

- Check for Home Assistant API changes
- Update dependencies
- Review and merge community contributions

**Quarterly:**

- Performance review
- Security audit
- Documentation updates

### Support Channels

1. **GitHub Issues** - Bug reports and feature requests
2. **Home Assistant Community Forum** - User discussions
3. **GitHub Discussions** - General questions
4. **Email** - Security issues only

### Update Policy

**Patch Releases (v1.0.x):**

- Bug fixes
- Security patches
- Documentation updates
- Released as needed

**Minor Releases (v1.x.0):**

- New features
- Non-breaking changes
- Performance improvements
- Released quarterly

**Major Releases (vX.0.0):**

- Breaking changes
- Major refactoring
- API changes
- Released annually

---

## Risk Assessment

### Technical Risks

| Risk                        | Impact | Probability | Mitigation                                  |
| --------------------------- | ------ | ----------- | ------------------------------------------- |
| API changes by Wiener Netze | High   | Medium      | Version API requests, monitor for changes   |
| OAuth2 complexity           | Medium | Low         | Use established libraries, thorough testing |
| Rate limiting               | Medium | Medium      | Implement caching, respect limits           |
| Token expiration handling   | Medium | Low         | Automatic refresh, user notification        |
| Data format changes         | Medium | Low         | Flexible parsing, validation                |

### Project Risks

| Risk               | Impact | Probability | Mitigation                  |
| ------------------ | ------ | ----------- | --------------------------- |
| Scope creep        | Medium | Medium      | Strict phase adherence      |
| Testing gaps       | High   | Low         | >90% coverage requirement   |
| Documentation lag  | Medium | Medium      | Document as you code        |
| Community adoption | Low    | Medium      | Good documentation, support |

---

## Success Metrics

### Technical Metrics

- Test coverage >90%
- Zero critical bugs in production
- API response time <2 seconds
- Memory usage <50MB
- Update reliability >99%

### User Metrics

- > 100 active installations (6 months)
- <5% bug reports per installation
- > 4.0 stars on HACS (if rated)
- Active community engagement

### Development Metrics

- Phase completion on schedule
- All acceptance criteria met
- Code review pass rate >90%
- CI/CD pipeline success rate >95%

---

## Resources Required

### Development

- Python 3.11+ environment
- Home Assistant test instance (2024.1+)
- Wiener Netze API access credentials:
  - Client ID
  - Client Secret
  - API Key
  - Test Zählpunkt (metering point ID)
- GitHub repository
- Access to WSTW Developer Portal for credential management

### Tools

- VS Code or PyCharm
- Git
- Docker (for HA testing)
- Postman/Insomnia (API testing)

### Documentation

- OpenAPI specification (provided)
- Home Assistant developer docs
- OAuth2 specification
- Python AsyncIO documentation

---

## Appendix

### A. Sensor Entity Specifications

#### Current Power Sensor

- **Entity ID:** `sensor.{meter_id}_current_power`
- **Device Class:** `power`
- **Unit:** W
- **State Class:** `measurement`
- **Update Interval:** 15 minutes

#### Daily Energy Sensor

- **Entity ID:** `sensor.{meter_id}_daily_energy`
- **Device Class:** `energy`
- **Unit:** kWh
- **State Class:** `total_increasing`
- **Reset:** Daily at midnight

#### Monthly Energy Sensor

- **Entity ID:** `sensor.{meter_id}_monthly_energy`
- **Device Class:** `energy`
- **Unit:** kWh
- **State Class:** `total`
- **Reset:** First day of month

### B. Configuration Options

```yaml
# Example configuration.yaml (for YAML-based config, if supported)
# NOTE: Config flow (UI-based configuration) is recommended
wiener_netze:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
  api_key: YOUR_API_KEY
  meter_points:
    - AT0010000000000000001000000000001
    - AT0010000000000000001000000000002
  update_interval: 15 # minutes
  data_granularity: "QUARTER_HOUR" # Options: QUARTER_HOUR, DAY, METER_READ
  result_type: "SMART_METER" # Options: ALL, SMART_METER
```

### How to Obtain API Credentials

1. **Register at WSTW Developer Portal**: https://api.wstw.at/
2. **Create an Application** in the developer portal
3. **Request API Access** by emailing `support.sm-portal@wienit.at` with:
   - Your application name from the WSTW Developer Portal
   - Your Smart Meter Portal email address
4. **Receive Credentials**: You will receive:
   - Client ID
   - Client Secret
   - API Key
5. **Configure Integration**: Enter these credentials in Home Assistant during setup

### C. API Rate Limits (To Be Determined)

**Assumptions (to be validated):**

- Max 60 requests per minute
- Max 1000 requests per day
- Implement exponential backoff for errors

### D. OBIS Codes Reference

Common OBIS codes in Wiener Netze responses:

- `1-0:1.8.0*255` - Total active energy import
- `1-0:2.8.0*255` - Total active energy export
- `1-0:16.7.0*255` - Current power

### E. Error Codes

Per API documentation, handle these HTTP status codes:

| Code | Meaning               | Description                                       | Action                      |
| ---- | --------------------- | ------------------------------------------------- | --------------------------- |
| 200  | OK                    | Request successful                                | Process response data       |
| 400  | Bad Request           | Incorrect query syntax or missing required params | Validate request parameters |
| 401  | Unauthorized          | Invalid or expired token                          | Refresh OAuth token         |
| 403  | Forbidden             | User not authorized to access resource            | Check API permissions       |
| 404  | Not Found             | API resource not found                            | Verify meter ID/endpoint    |
| 408  | Request Timeout       | Request took too long                             | Retry with timeout handling |
| 500  | Internal Server Error | Unexpected server error                           | Retry with backoff          |

### F. Development Timeline (Gantt Chart)

```
Week 1-2:  [████████████] Phase 1: Foundation
Week 2-3:  [████████████] Phase 2: Config Flow
Week 3-4:  [████████████] Phase 3: Data Coordinator
Week 4-5:  [████████████] Phase 4: Sensor Implementation
Week 5-6:  [████████████] Phase 5: Testing & Refinement
Week 6-7:  [████████████] Phase 6: Documentation & Release
Week 7-8:  [████████████] Phase 7: Community Release
```

---

## Revision History

| Version | Date       | Author  | Changes                     |
| ------- | ---------- | ------- | --------------------------- |
| 1.0     | 2025-11-09 | Initial | Initial implementation plan |

---

## Approval

This implementation plan should be reviewed and approved by:

- [ ] Project Lead
- [ ] Technical Architect
- [ ] QA Lead
- [ ] Documentation Lead

**Last Updated:** November 9, 2025
