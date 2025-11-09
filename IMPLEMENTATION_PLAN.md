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

### In Scope

✅ **Core Features:**

- OAuth2 authentication with Wiener Netze API
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
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Wiener Netze Integration                    │  │
│  │                                                     │  │
│  │  ┌──────────────┐      ┌────────────────────────┐ │  │
│  │  │ Config Flow  │      │   Data Coordinator     │ │  │
│  │  │  (OAuth2)    │      │  (Update Handler)      │ │  │
│  │  └──────────────┘      └────────────────────────┘ │  │
│  │         │                        │                 │  │
│  │         │                        │                 │  │
│  │  ┌──────▼────────────────────────▼──────────────┐ │  │
│  │  │           API Client Library                 │ │  │
│  │  │  (Authentication, Rate Limiting, Caching)    │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  │         │                                          │  │
│  └─────────┼──────────────────────────────────────────┘  │
│            │                                              │
│  ┌─────────▼──────────────────────────────────────────┐  │
│  │              Sensor Entities                       │  │
│  │  • Current Consumption  • Daily Total              │  │
│  │  • Meter Reading       • Historical Data          │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS / OAuth2
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Wiener Netze Smart Meter API                   │
│      https://api.wstw.at/gateway/WN_SMART_METER_API/1.0    │
│                                                             │
│  • /zaehlpunkte              (List metering points)        │
│  • /zaehlpunkte/{id}         (Get specific meter)          │
│  • /zaehlpunkte/messwerte    (Get consumption data)        │
│  • /zaehlpunkte/{id}/messwerte (Get meter-specific data)   │
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

- `resultType` (optional)
- `zaehlpunkt` (optional) - Filter by specific meter
- `webProfileId` (optional)

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

- `datumVon` - Start date
- `datumBis` - End date
- `wertetyp` - Value type (15MIN, HOUR, DAY, MONTH, YEAR)

**Optional Parameters:**

- `zaehlpunkt` - Filter by specific meter
- `webProfileId`

**Use Case:** Batch retrieval for multiple meters

#### 4. Get Consumption Data (Specific Meter)

**Endpoint:** `GET /zaehlpunkte/{zaehlpunkt}/messwerte`
**Required Parameters:**

- `zaehlpunkt` (path) - Meter ID
- `datumVon` - Start date
- `datumBis` - End date
- `wertetyp` - Value type

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

### Data Types (wertetyp)

- `15MIN` - 15-minute intervals (most granular)
- `HOUR` - Hourly data
- `DAY` - Daily totals
- `MONTH` - Monthly totals
- `YEAR` - Yearly totals

### Authentication

**Type:** OAuth2
**Security Schemes:**

- `x-Gateway-APIKey` - API Key in header
- `OAUTH2` - OAuth2 flow

**Requirements:**

- Client credentials (to be obtained from Wiener Netze)
- Token refresh mechanism
- Secure storage of tokens in Home Assistant

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
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/yourusername/WienerNetzeHomeAssist",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/yourusername/WienerNetzeHomeAssist/issues",
  "requirements": ["aiohttp>=3.9.0"],
  "version": "1.0.0"
}
```

#### `const.py`

Central location for all constants.

```python
DOMAIN = "wiener_netze"
CONF_METER_POINTS = "meter_points"
DEFAULT_UPDATE_INTERVAL = 15  # minutes
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_AUTHORIZE_URL = "..."
OAUTH_TOKEN_URL = "..."
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

1. OAuth2 authentication
2. Meter selection (if multiple available)
3. Configuration confirmation
4. Options for update interval

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Objectives:**

- Set up project structure
- Implement basic API client
- Create authentication flow

**Tasks:**

1. Create directory structure and files
2. Set up development environment
3. Implement `api.py` with basic HTTP client
4. Implement OAuth2 authentication in `oauth2.py`
5. Create `manifest.json` and `const.py`
6. Write initial unit tests for API client
7. Document API client usage

**Deliverables:**

- ✅ Working API client that can authenticate
- ✅ Ability to fetch metering points
- ✅ Basic error handling
- ✅ Unit tests with >80% coverage

**Acceptance Criteria:**

- API client successfully authenticates with Wiener Netze
- Can retrieve list of metering points
- All HTTP errors are properly caught and handled
- Tests pass

---

### Phase 2: Config Flow (Week 2-3)

**Objectives:**

- Create user-friendly setup experience
- Handle OAuth2 flow in Home Assistant
- Allow meter selection

**Tasks:**

1. Implement `config_flow.py` with OAuth2 flow
2. Create user steps for authentication
3. Implement meter selection interface
4. Add options flow for update interval
5. Create translations (`strings.json`, `en.json`, `de.json`)
6. Write config flow tests
7. Test with actual Home Assistant instance

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
- Home Assistant test instance
- Wiener Netze API access credentials
- GitHub repository

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
wiener_netze:
  client_id: YOUR_CLIENT_ID
  client_secret: YOUR_CLIENT_SECRET
  meter_points:
    - AT0010000000000000001000000000001
    - AT0010000000000000001000000000002
  update_interval: 15 # minutes
  data_granularity: "15MIN"
```

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

| Code | Meaning      | Action                      |
| ---- | ------------ | --------------------------- |
| 400  | Bad Request  | Validate request parameters |
| 401  | Unauthorized | Refresh OAuth token         |
| 403  | Forbidden    | Check API permissions       |
| 404  | Not Found    | Verify meter ID             |
| 500  | Server Error | Retry with backoff          |

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
