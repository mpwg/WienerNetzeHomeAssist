# Task 05: API Client - Basic Structure

**Category:** API Client Development
**Priority:** High
**Estimated Effort:** 3-4 hours
**Status:** Not Started

## Description

Create the basic structure for the Wiener Netze Smart Meter API client, including authentication handling, HTTP client setup, and error classes.

## Prerequisites

- **Task 02** completed (Repository Structure Setup)
- OpenAPI specification reviewed (`dokumentation/Export_WN_SMART_METER_API.yaml`)
- API documentation reviewed (`dokumentation/wn.md`)

## Objectives

1. Create API client class structure
2. Implement HTTP client with aiohttp
3. Define custom exception classes
4. Implement OAuth2 authentication
5. Add request/response logging

## Deliverables

- [ ] `custom_components/wiener_netze/api.py` with base client
- [ ] Custom exception classes defined
- [ ] OAuth2 authentication implemented
- [ ] HTTP client configured with timeouts
- [ ] Basic unit tests for API client

## Steps

### 1. Define Exception Classes

```python
"""Exceptions for Wiener Netze API."""


class WienerNetzeApiError(Exception):
    """Base exception for Wiener Netze API errors."""


class WienerNetzeAuthError(WienerNetzeApiError):
    """Authentication error."""


class WienerNetzeConnectionError(WienerNetzeApiError):
    """Connection error."""


class WienerNetzeTimeoutError(WienerNetzeApiError):
    """Request timeout error."""


class WienerNetzeRateLimitError(WienerNetzeApiError):
    """Rate limit exceeded error."""


class WienerNetzeNotFoundError(WienerNetzeApiError):
    """Resource not found error."""


class WienerNetzeBadRequestError(WienerNetzeApiError):
    """Bad request error."""
```

### 2. Create API Client Base Structure

```python
"""API client for Wiener Netze Smart Meter."""
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout

_LOGGER = logging.getLogger(__name__)

# API Constants
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://api.wstw.at/oauth2/token"
DEFAULT_TIMEOUT = 30
RETRY_ATTEMPTS = 3


class WienerNetzeApiClient:
    """Client for Wiener Netze Smart Meter API."""

    def __init__(
        self,
        session: ClientSession,
        client_id: str,
        client_secret: str,
        api_key: str,
    ) -> None:
        """Initialize the API client.

        Args:
            session: aiohttp ClientSession
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            api_key: API Gateway key
        """
        self._session = session
        self._client_id = client_id
        self._client_secret = client_secret
        self._api_key = api_key

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        _LOGGER.debug("Wiener Netze API client initialized")

    @property
    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "x-Gateway-APIKey": self._api_key,
            "Content-Type": "application/json",
        }

        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    async def _ensure_token(self) -> None:
        """Ensure we have a valid access token."""
        if self._access_token and self._token_expires_at:
            # Check if token is still valid (with 5 minute buffer)
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return

        # Token missing or expired, authenticate
        await self.authenticate()

    async def authenticate(self) -> None:
        """Authenticate with OAuth2 and obtain access token."""
        _LOGGER.debug("Authenticating with Wiener Netze API")

        try:
            timeout = ClientTimeout(total=DEFAULT_TIMEOUT)

            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }

            async with self._session.post(
                OAUTH_TOKEN_URL,
                data=data,
                timeout=timeout,
            ) as response:
                if response.status == 401:
                    raise WienerNetzeAuthError("Invalid credentials")

                if response.status != 200:
                    text = await response.text()
                    raise WienerNetzeAuthError(
                        f"Authentication failed: {response.status} - {text}"
                    )

                result = await response.json()

                self._access_token = result["access_token"]
                expires_in = result.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

                _LOGGER.info("Successfully authenticated with Wiener Netze API")

        except aiohttp.ClientError as err:
            raise WienerNetzeConnectionError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise WienerNetzeTimeoutError("Authentication timeout") from err

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base URL)
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Response JSON data

        Raises:
            WienerNetzeApiError: On API errors
        """
        await self._ensure_token()

        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        timeout = ClientTimeout(total=DEFAULT_TIMEOUT)

        _LOGGER.debug("API request: %s %s", method, url)

        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers,
                timeout=timeout,
                **kwargs,
            ) as response:
                # Log response status
                _LOGGER.debug("API response: %s %s", response.status, url)

                # Handle error responses
                if response.status == 400:
                    text = await response.text()
                    raise WienerNetzeBadRequestError(f"Bad request: {text}")

                if response.status == 401:
                    # Token might be invalid, try to re-authenticate once
                    _LOGGER.warning("Access token invalid, re-authenticating")
                    self._access_token = None
                    await self._ensure_token()
                    # Retry request
                    return await self._request(method, endpoint, **kwargs)

                if response.status == 403:
                    raise WienerNetzeAuthError("Forbidden: insufficient permissions")

                if response.status == 404:
                    raise WienerNetzeNotFoundError("Resource not found")

                if response.status == 408:
                    raise WienerNetzeTimeoutError("Request timeout")

                if response.status == 429:
                    raise WienerNetzeRateLimitError("Rate limit exceeded")

                if response.status >= 500:
                    text = await response.text()
                    raise WienerNetzeApiError(f"Server error: {response.status} - {text}")

                if response.status != 200:
                    text = await response.text()
                    raise WienerNetzeApiError(
                        f"Unexpected response: {response.status} - {text}"
                    )

                return await response.json()

        except aiohttp.ClientError as err:
            raise WienerNetzeConnectionError(f"Connection error: {err}") from err
        except asyncio.TimeoutError as err:
            raise WienerNetzeTimeoutError(f"Request timeout: {err}") from err

    async def _get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def _post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, **kwargs)
```

### 3. Add to const.py

```python
"""Constants for Wiener Netze integration."""

DOMAIN = "wiener_netze"

# API Configuration
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://api.wstw.at/oauth2/token"
API_TIMEOUT = 30

# Configuration Keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_KEY = "api_key"

# Update Interval
DEFAULT_SCAN_INTERVAL = 15  # minutes

# API Parameters
GRANULARITY_QUARTER_HOUR = "QUARTER_HOUR"
GRANULARITY_DAY = "DAY"
GRANULARITY_METER_READ = "METER_READ"

RESULT_TYPE_SMART_METER = "SMART_METER"
RESULT_TYPE_ALL = "ALL"

# Quality Indicators
QUALITY_VAL = "VAL"  # Validated actual value
QUALITY_EST = "EST"  # Estimated/calculated value
```

### 4. Create Unit Tests

**tests/test_api.py:**

```python
"""Test API client."""
import pytest
from aiohttp import ClientSession
from unittest.mock import AsyncMock, patch, MagicMock

from custom_components.wiener_netze.api import (
    WienerNetzeApiClient,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
    WienerNetzeNotFoundError,
)
from tests.utils import load_json_fixture


@pytest.fixture
def api_client(aiohttp_client):
    """Return API client."""
    session = MagicMock(spec=ClientSession)
    return WienerNetzeApiClient(
        session=session,
        client_id="test_client",
        client_secret="test_secret",
        api_key="test_key",
    )


async def test_authenticate_success(api_client):
    """Test successful authentication."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "access_token": "test_token",
        "expires_in": 3600,
    })

    api_client._session.post = AsyncMock(return_value=mock_response)

    await api_client.authenticate()

    assert api_client._access_token == "test_token"
    assert api_client._token_expires_at is not None


async def test_authenticate_invalid_credentials(api_client):
    """Test authentication with invalid credentials."""
    mock_response = AsyncMock()
    mock_response.status = 401

    api_client._session.post = AsyncMock(return_value=mock_response)

    with pytest.raises(WienerNetzeAuthError):
        await api_client.authenticate()


async def test_headers_without_token(api_client):
    """Test headers without access token."""
    headers = api_client._headers

    assert headers["x-Gateway-APIKey"] == "test_key"
    assert "Authorization" not in headers


async def test_headers_with_token(api_client):
    """Test headers with access token."""
    api_client._access_token = "test_token"
    headers = api_client._headers

    assert headers["x-Gateway-APIKey"] == "test_key"
    assert headers["Authorization"] == "Bearer test_token"
```

## Acceptance Criteria

- [ ] API client class created with proper structure
- [ ] All exception classes defined
- [ ] OAuth2 authentication implemented
- [ ] Request method with error handling
- [ ] HTTP headers correctly set (dual authentication)
- [ ] Token expiration handling
- [ ] Proper logging throughout
- [ ] Unit tests passing (>80% coverage)

## Testing

```bash
# Run API client tests
pytest tests/test_api.py -v

# Check coverage
pytest tests/test_api.py --cov=custom_components.wiener_netze.api --cov-report=term-missing

# Test with specific test
pytest tests/test_api.py::test_authenticate_success -v
```

## References

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [OAuth2 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- [Wiener Netze API Documentation](../dokumentation/Export_WN_SMART_METER_API.yaml)

## Notes

- Use asyncio for all I/O operations
- Implement automatic token refresh before expiration
- Dual authentication: OAuth2 Bearer + x-Gateway-APIKey header
- Log all requests/responses at debug level
- Handle all documented HTTP status codes (400, 401, 403, 404, 408, 500)

## Next Task

→ **Task 06:** API Client - Meter Points Retrieval
