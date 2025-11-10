# Task 05 Completion: API Client - Basic Structure

**Date:** November 10, 2025
**Status:** ✅ Completed

## Overview

Successfully created the basic structure for the Wiener Netze Smart Meter API client, including comprehensive authentication handling, HTTP client setup with aiohttp, and custom exception classes.

## Deliverables Completed

### 1. Exception Classes (api.py)

Created a complete exception hierarchy for API error handling:

```python
- WienerNetzeApiError (Base exception)
  ├── WienerNetzeAuthError (Authentication errors)
  ├── WienerNetzeConnectionError (Connection errors)
  ├── WienerNetzeTimeoutError (Timeout errors)
  ├── WienerNetzeRateLimitError (Rate limit errors)
  ├── WienerNetzeNotFoundError (404 errors)
  └── WienerNetzeBadRequestError (400 errors)
```

**Benefits:**

- Clear exception hierarchy for error handling
- Specific exceptions for different error scenarios
- Easy to catch and handle specific error types in calling code

### 2. API Client Base Structure

**Class:** `WienerNetzeApiClient`

**Key Features:**

- Async/await throughout (using aiohttp)
- Dual authentication (OAuth2 Bearer + x-Gateway-APIKey)
- Automatic token management and refresh
- Comprehensive error handling
- Request/response logging

**Initialization Parameters:**

```python
- session: ClientSession (aiohttp session)
- client_id: OAuth2 client ID
- client_secret: OAuth2 client secret
- api_key: API Gateway key
```

### 3. OAuth2 Authentication Implementation

**Method:** `authenticate()`

**Features:**

- OAuth2 client credentials flow
- Token expiration tracking
- Automatic token refresh (5-minute buffer)
- Error handling for invalid credentials
- Connection and timeout error handling

**Token Management:**

```python
- _access_token: Stores the Bearer token
- _token_expires_at: Tracks token expiration
- _ensure_token(): Ensures valid token before requests
```

**Token Refresh Logic:**

- Checks token validity before each request
- Refreshes if expired or missing
- 5-minute buffer before expiration
- Automatic retry on 401 responses

### 4. HTTP Request Infrastructure

**Method:** `_request(method, endpoint, **kwargs)`

**Features:**

- Generic request method with retry logic
- Automatic token management
- Comprehensive HTTP status code handling
- Request/response logging
- Configurable timeout (30 seconds default)

**HTTP Status Code Handling:**

- ✅ 200: Success
- ❌ 400: Bad Request → `WienerNetzeBadRequestError`
- ❌ 401: Unauthorized → Re-authenticate and retry
- ❌ 403: Forbidden → `WienerNetzeAuthError`
- ❌ 404: Not Found → `WienerNetzeNotFoundError`
- ❌ 408: Timeout → `WienerNetzeTimeoutError`
- ❌ 429: Rate Limit → `WienerNetzeRateLimitError`
- ❌ 5xx: Server Error → `WienerNetzeApiError`

**Helper Methods:**

```python
- _get(endpoint, **kwargs): GET request wrapper
- _post(endpoint, **kwargs): POST request wrapper
```

### 5. Dual Authentication Headers

**Property:** `_headers`

Returns headers with both authentication methods:

```python
{
    "x-Gateway-APIKey": "<api_key>",
    "Content-Type": "application/json",
    "Authorization": "Bearer <access_token>"  # When token available
}
```

### 6. Updated Constants (const.py)

Added comprehensive API configuration constants:

**API Configuration:**

```python
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://api.wstw.at/oauth2/token"
API_TIMEOUT = 30
```

**Configuration Keys:**

```python
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_KEY = "api_key"
```

**Update Interval:**

```python
DEFAULT_SCAN_INTERVAL = 15  # minutes
```

**API Parameters:**

```python
GRANULARITY_QUARTER_HOUR = "QUARTER_HOUR"
GRANULARITY_DAY = "DAY"
GRANULARITY_METER_READ = "METER_READ"

RESULT_TYPE_SMART_METER = "SMART_METER"
RESULT_TYPE_ALL = "ALL"
```

**Quality Indicators:**

```python
QUALITY_VAL = "VAL"  # Validated actual value
QUALITY_EST = "EST"  # Estimated/calculated value
```

### 7. Comprehensive Unit Tests

**File:** `tests/test_api.py`

**Test Classes:**

1. `TestApiClientInitialization` - Client setup and header tests
2. `TestAuthentication` - OAuth2 authentication scenarios
3. `TestApiRequests` - HTTP request handling and error scenarios

**Test Coverage:** 98% (97/99 statements)

**Tests Implemented (23 total):**

#### Initialization Tests (3)

- ✅ Client initialization
- ✅ Headers without token
- ✅ Headers with token

#### Authentication Tests (8)

- ✅ Successful authentication
- ✅ Invalid credentials (401)
- ✅ Server error during auth
- ✅ Connection error
- ✅ Timeout error
- ✅ Token validity check (no re-auth needed)
- ✅ Expired token (triggers re-auth)
- ✅ Missing token (triggers auth)

#### API Request Tests (12)

- ✅ Successful request (200)
- ✅ Bad request (400)
- ✅ Unauthorized with retry (401)
- ✅ Forbidden (403)
- ✅ Not found (404)
- ✅ Request timeout (408)
- ✅ Rate limit (429)
- ✅ Server error (500+)
- ✅ Connection error exception
- ✅ Timeout exception
- ✅ GET method wrapper
- ✅ POST method wrapper

## Technical Implementation Details

### Architecture Decisions

1. **Async/Await Design**

   - All I/O operations use async/await
   - Compatible with Home Assistant's async architecture
   - Non-blocking API calls

2. **Token Management Strategy**

   - Proactive token refresh (5-minute buffer)
   - Automatic retry on 401 responses
   - Minimal authentication overhead

3. **Error Handling Philosophy**

   - Specific exceptions for different error types
   - Automatic retry only for 401 (token expiration)
   - Clear error messages with context

4. **Logging Strategy**
   - Debug level for requests/responses
   - Info level for successful authentication
   - Warning level for token re-authentication

### Security Considerations

1. **Dual Authentication**

   - OAuth2 Bearer token for user authorization
   - API Gateway key for service identification
   - Both required for API access

2. **Token Security**

   - Tokens stored in memory only
   - No token persistence in this layer
   - Automatic expiration handling

3. **Credential Handling**
   - Credentials passed at initialization
   - Not logged or exposed in errors
   - Used only for authentication requests

## Files Modified/Created

### Created

- None (files already existed from previous tasks)

### Modified

```
custom_components/wiener_netze/
├── api.py (229 lines) - Complete API client implementation
├── const.py (31 lines) - Added API constants

tests/
├── test_api.py (364 lines) - Comprehensive test suite
```

## Testing Results

### Test Execution

```bash
pytest tests/test_api.py -v
```

**Result:** ✅ 23 tests passed (0.19s)

### Code Coverage

```bash
pytest tests/test_api.py --cov=custom_components.wiener_netze.api --cov-report=term-missing
```

**Result:** ✅ 98% coverage (97/99 statements)

- Only uncovered: Unexpected response status codes (catch-all error handler)

## Acceptance Criteria

- ✅ API client class created with proper structure
- ✅ All exception classes defined
- ✅ OAuth2 authentication implemented
- ✅ Request method with error handling
- ✅ HTTP headers correctly set (dual authentication)
- ✅ Token expiration handling
- ✅ Proper logging throughout
- ✅ Unit tests passing (98% coverage > 80% requirement)

## Integration Points

### With Home Assistant

- Uses `aiohttp.ClientSession` from HA core
- Compatible with HA's async event loop
- Follows HA integration patterns

### With Config Flow (Future)

- Client initialization from config entry data
- Credentials from user input

### With Coordinator (Future)

- Client provides data fetching methods
- Error exceptions for coordinator error handling

### With Sensors (Future)

- Client retrieves consumption data
- Data transformation in coordinator

## API Documentation Reference

Based on `dokumentation/Export_WN_SMART_METER_API.yaml`:

**Base URL:** `https://api.wstw.at/gateway/WN_SMART_METER_API/1.0`

**Authentication:**

- OAuth2 Token URL: `https://api.wstw.at/oauth2/token`
- Grant Type: `client_credentials`
- Required Headers:
  - `Authorization: Bearer <token>`
  - `x-Gateway-APIKey: <api_key>`

**Endpoints (to be implemented in next tasks):**

- `/zaehlpunkte` - Get meter points
- `/messdaten/zaehlpunkt/{zaehlpunkt}` - Get consumption data

## Known Limitations

1. **No Retry Logic**

   - Except for 401 (automatic re-auth)
   - Rate limiting handled with exception only
   - Connection errors not automatically retried

2. **Fixed Timeout**

   - 30 seconds for all requests
   - Not configurable at runtime
   - Could be parameterized in future

3. **No Response Caching**

   - Every request hits the API
   - Caching handled by coordinator layer
   - API provides fresh data each time

4. **Single OAuth2 Flow**
   - Only client_credentials grant type
   - No user authorization flow
   - Sufficient for current requirements

## Future Enhancements

### Short-term (Next Tasks)

- Implement meter points retrieval (Task 06)
- Implement consumption data retrieval (Task 07)
- Add request/response data validation

### Long-term

- Add exponential backoff retry logic
- Implement request rate limiting
- Add response caching layer
- Support additional OAuth2 flows
- Configurable timeouts
- Request metrics and monitoring

## Lessons Learned

1. **Mock Context Managers:** Required `__aenter__` and `__aexit__` for async context managers in tests
2. **Token Buffer:** 5-minute buffer prevents token expiration during long-running requests
3. **Specific Exceptions:** Granular exceptions enable better error handling in calling code
4. **Dual Auth Headers:** Both OAuth2 and API key required for Wiener Netze API
5. **Retry on 401:** Automatic token refresh improves reliability

## References

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [OAuth2 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- [Wiener Netze API Documentation](dokumentation/Export_WN_SMART_METER_API.yaml)
- [Home Assistant Integration Development](https://developers.home-assistant.io/docs/api/rest/)

## Next Steps

**Immediate:**

- Commit changes to repository
- Move to Task 06

**Task 06:** API Client - Meter Points Retrieval

- Implement `get_meter_points()` method
- Parse meter point data
- Add tests for meter point retrieval

**Task 07:** API Client - Consumption Data Retrieval

- Implement `get_consumption_data()` method
- Support different granularities
- Add tests for consumption data

## Conclusion

Task 05 successfully completed. The API client base structure is fully implemented with:

- ✅ Robust OAuth2 authentication
- ✅ Comprehensive error handling
- ✅ Dual authentication support
- ✅ 98% test coverage
- ✅ Production-ready code quality

The client provides a solid foundation for implementing specific API endpoints in subsequent tasks.

---

**Previous Task:** [Task 04 - HACS Configuration Setup](TASK_04_COMPLETION.md)
**Next Task:** Task 06 - API Client - Meter Points Retrieval
