# Agents Documentation

## Project Overview

This repository contains a Home Assistant integration for Wiener Netze Smart Meters, enabling real-time energy consumption monitoring directly in Home Assistant.

## Coding Agents

### Agent Capabilities

When working with AI coding agents (GitHub Copilot, Cursor, etc.) on this project, they can assist with:

1. **Integration Development**

   - Implementing OAuth2 authentication flow with Wiener Netze API
   - Creating sensor entities for energy consumption data
   - Building config flow for user setup
   - Implementing data update coordinators

2. **API Client Development**

   - Creating Python API client for Wiener Netze Smart Meter API
   - Handling rate limiting and error recovery
   - Parsing and transforming API responses
   - Managing authentication tokens

3. **Testing**

   - Writing unit tests for API client
   - Creating integration tests for Home Assistant component
   - Mocking API responses for testing
   - Implementing test fixtures

4. **Documentation**
   - Generating API documentation
   - Writing user setup guides
   - Creating technical documentation
   - Documenting configuration options

### Agent Guidelines

When using coding agents on this project:

#### Context Provision

- Always provide the OpenAPI specification (`dokumentation/Export_WN_SMART_METER_API.yaml`)
- Reference Home Assistant integration documentation
- Include relevant error messages and logs
- Share configuration examples

#### Code Standards

- Follow Home Assistant integration guidelines
- Use type hints in Python code
- Implement proper error handling
- Include logging statements
- Follow PEP 8 style guide

#### Security Considerations

- Never hardcode credentials or API keys
- Use Home Assistant's secure storage for tokens
- Validate all user inputs
- Handle sensitive data appropriately
- Implement proper OAuth2 flows

#### Testing Requirements

- Request tests for all new functionality
- Ensure test coverage for error cases
- Mock external API calls
- Test configuration flows
- Validate sensor data transformations

### Recommended Agent Workflows

#### 1. Initial Setup

```
Agent Task: "Set up the basic Home Assistant integration structure following
the official integration template. Include manifest.json, __init__.py,
config_flow.py, and sensor.py files."
```

#### 2. API Client Development

```
Agent Task: "Create a Python API client for the Wiener Netze Smart Meter API
based on the OpenAPI specification in dokumentation/Export_WN_SMART_METER_API.yaml.
Include OAuth2 authentication, error handling, and rate limiting."
```

#### 3. Sensor Implementation

```
Agent Task: "Implement Home Assistant sensor entities for energy consumption
data from Wiener Netze Smart Meters. Create sensors for current consumption,
daily totals, and meter readings."
```

#### 4. Configuration Flow

```
Agent Task: "Create a config flow that guides users through OAuth2 authentication
with Wiener Netze API and selection of their smart meter (Zählpunkt)."
```

#### 5. Testing

```
Agent Task: "Generate comprehensive unit tests for the API client and integration
tests for the Home Assistant component. Include fixtures for mocking API responses."
```

### Common Agent Commands

#### Code Generation

- "Implement the OAuth2 authentication flow using aiohttp"
- "Create sensor entities that update every 15 minutes"
- "Add error handling for API timeout scenarios"
- "Generate type hints for all function signatures"

#### Refactoring

- "Refactor the API client to use async/await properly"
- "Extract configuration constants to a separate file"
- "Split the sensor.py file into multiple sensor classes"
- "Improve error messages for better debugging"

#### Documentation

- "Generate docstrings for all public methods"
- "Create a README with setup instructions"
- "Document the OAuth2 setup process for users"
- "Add inline comments explaining the rate limiting logic"

#### Testing

- "Create unit tests for the API client's error handling"
- "Generate mock responses based on the OpenAPI spec"
- "Add integration tests for the config flow"
- "Create fixtures for common test scenarios"

## Agent Limitations

Be aware of these limitations when working with coding agents:

1. **API Understanding**: Agents may not fully understand Wiener Netze-specific API quirks
2. **OAuth2 Flow**: Complex OAuth2 implementations may require human review
3. **Home Assistant APIs**: May need guidance on latest HA integration patterns
4. **German Language**: Some API responses are in German; clarify translations
5. **Rate Limits**: Agents won't know Wiener Netze's actual rate limits

## Best Practices

### Before Agent Interaction

- [ ] Read the implementation plan
- [ ] Review Home Assistant integration documentation
- [ ] Understand the Wiener Netze API endpoints
- [ ] Prepare test credentials (if available)

### During Agent Interaction

- [ ] Provide clear, specific prompts
- [ ] Review generated code before committing
- [ ] Test functionality in a development environment
- [ ] Validate against the OpenAPI specification
- [ ] Check for security vulnerabilities

### After Agent Interaction

- [ ] Run linters and formatters
- [ ] Execute test suite
- [ ] Review code for HA best practices
- [ ] Update documentation
- [ ] Test in a real Home Assistant instance

## Resources

### Home Assistant

- [Integration Development](https://developers.home-assistant.io/docs/creating_component_index)
- [Config Flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Sensor Platform](https://developers.home-assistant.io/docs/core/entity/sensor)
- [OAuth2 Implementation](https://developers.home-assistant.io/docs/api_lib_auth)

### Wiener Netze

- API Base URL: `https://api.wstw.at/gateway/WN_SMART_METER_API/1.0`
- API Documentation: `dokumentation/Export_WN_SMART_METER_API.yaml`
- Support: support.sm-portal@wienit.at

### Python Libraries

- `aiohttp` for async HTTP requests
- `homeassistant` for HA integration APIs
- `pytest` for testing
- `pytest-homeassistant-custom-component` for HA testing

## Troubleshooting Agent Issues

### Agent produces outdated HA code

**Solution**: Explicitly mention "use Home Assistant 2024+ integration patterns"

### Agent doesn't handle OAuth2 correctly

**Solution**: Provide specific OAuth2 flow documentation or examples

### Agent generates synchronous code

**Solution**: Emphasize "use async/await for all I/O operations"

### Agent ignores OpenAPI spec

**Solution**: Include relevant sections of the spec in your prompt

### Agent creates insecure code

**Solution**: Request security review and specify "follow OWASP guidelines"

## Contributing

When contributing code generated by agents:

1. Thoroughly review all generated code
2. Run the test suite
3. Validate against security best practices
4. Ensure code follows project standards
5. Test in a real Home Assistant environment
6. Update documentation as needed

## Version Control

- Commit agent-generated code in small, logical chunks
- Write meaningful commit messages explaining what was generated
- Tag commits that used AI assistance (optional)
- Review diffs carefully before pushing

## License

This integration is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). The Wiener Netze API is licensed under CC BY-NC-ND 4.0.

**Important License Considerations:**

- This is a copyleft license that requires sharing source code
- If you modify and deploy this integration on a network server, you must make the source code available
- Any modifications or derivative works must also be licensed under AGPL-3.0
- See LICENSE.md for full license text
