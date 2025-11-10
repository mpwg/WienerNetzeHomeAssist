"""Tests for api.py."""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp import ClientSession

from custom_components.wiener_netze.api import (
    WienerNetzeApiClient,
    WienerNetzeApiError,
    WienerNetzeAuthError,
    WienerNetzeBadRequestError,
    WienerNetzeConnectionError,
    WienerNetzeNotFoundError,
    WienerNetzeRateLimitError,
    WienerNetzeTimeoutError,
)
from tests.utils import load_json_fixture


@pytest.fixture
def mock_session():
    """Return mock aiohttp session."""
    return MagicMock(spec=ClientSession)


@pytest.fixture
def api_client(mock_session):
    """Return API client."""
    return WienerNetzeApiClient(
        session=mock_session,
        client_id="test_client",
        client_secret="test_secret",
        api_key="test_key",
    )


class TestApiClientInitialization:
    """Tests for API client initialization."""

    def test_client_initialization(self, api_client):
        """Test client is properly initialized."""
        assert api_client._client_id == "test_client"
        assert api_client._client_secret == "test_secret"
        assert api_client._api_key == "test_key"
        assert api_client._access_token is None
        assert api_client._token_expires_at is None

    def test_headers_without_token(self, api_client):
        """Test headers without access token."""
        headers = api_client._headers

        assert headers["x-Gateway-APIKey"] == "test_key"
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_headers_with_token(self, api_client):
        """Test headers with access token."""
        api_client._access_token = "test_token"
        headers = api_client._headers

        assert headers["x-Gateway-APIKey"] == "test_key"
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test_token"


class TestAuthentication:
    """Tests for authentication."""

    async def test_authenticate_success(self, api_client, mock_session):
        """Test successful authentication."""
        token_data = load_json_fixture("oauth_token.json")

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        await api_client.authenticate()

        assert api_client._access_token == token_data["access_token"]
        assert api_client._token_expires_at is not None

        # Verify post was called with correct parameters
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert "client_id" in call_args.kwargs["data"]
        assert call_args.kwargs["data"]["grant_type"] == "client_credentials"

    async def test_authenticate_invalid_credentials(self, api_client, mock_session):
        """Test authentication with invalid credentials."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeAuthError, match="Invalid credentials"):
            await api_client.authenticate()

    async def test_authenticate_server_error(self, api_client, mock_session):
        """Test authentication with server error."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeAuthError, match="Authentication failed"):
            await api_client.authenticate()

    async def test_authenticate_connection_error(self, api_client, mock_session):
        """Test authentication with connection error."""
        mock_session.post = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        with pytest.raises(WienerNetzeConnectionError, match="Connection error"):
            await api_client.authenticate()

    async def test_authenticate_timeout(self, api_client, mock_session):
        """Test authentication timeout."""
        mock_session.post = MagicMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(WienerNetzeTimeoutError, match="Authentication timeout"):
            await api_client.authenticate()

    async def test_ensure_token_valid(self, api_client):
        """Test ensure_token with valid token."""
        api_client._access_token = "valid_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        # Should not call authenticate
        with patch.object(api_client, "authenticate") as mock_auth:
            await api_client._ensure_token()
            mock_auth.assert_not_called()

    async def test_ensure_token_expired(self, api_client, mock_session):
        """Test ensure_token with expired token."""
        api_client._access_token = "expired_token"
        api_client._token_expires_at = datetime.now() - timedelta(hours=1)

        token_data = load_json_fixture("oauth_token.json")
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        await api_client._ensure_token()

        assert api_client._access_token == token_data["access_token"]

    async def test_ensure_token_missing(self, api_client, mock_session):
        """Test ensure_token with missing token."""
        token_data = load_json_fixture("oauth_token.json")
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=token_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        await api_client._ensure_token()

        assert api_client._access_token == token_data["access_token"]


class TestApiRequests:
    """Tests for API requests."""

    async def test_request_success(self, api_client, mock_session):
        """Test successful API request."""
        # Setup token
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client._request("GET", "/test")

        assert result == {"data": "test"}
        mock_session.request.assert_called_once()

    async def test_request_bad_request(self, api_client, mock_session):
        """Test API request with bad request error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeBadRequestError, match="Bad request"):
            await api_client._request("GET", "/test")

    async def test_request_unauthorized_retry(self, api_client, mock_session):
        """Test API request retry on 401."""
        api_client._access_token = "expired_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        # First response: 401 (unauthorized)
        mock_response_401 = AsyncMock()
        mock_response_401.status = 401
        mock_response_401.__aenter__ = AsyncMock(return_value=mock_response_401)
        mock_response_401.__aexit__ = AsyncMock(return_value=None)

        # Second response: 200 (success after re-auth)
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={"data": "test"})
        mock_response_200.__aenter__ = AsyncMock(return_value=mock_response_200)
        mock_response_200.__aexit__ = AsyncMock(return_value=None)

        # OAuth token response
        token_data = load_json_fixture("oauth_token.json")
        mock_token_response = AsyncMock()
        mock_token_response.status = 200
        mock_token_response.json = AsyncMock(return_value=token_data)
        mock_token_response.__aenter__ = AsyncMock(return_value=mock_token_response)
        mock_token_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(
            side_effect=[mock_response_401, mock_response_200]
        )
        mock_session.post = MagicMock(return_value=mock_token_response)

        result = await api_client._request("GET", "/test")

        assert result == {"data": "test"}
        assert mock_session.request.call_count == 2

    async def test_request_forbidden(self, api_client, mock_session):
        """Test API request with forbidden error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 403
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeAuthError, match="Forbidden"):
            await api_client._request("GET", "/test")

    async def test_request_not_found(self, api_client, mock_session):
        """Test API request with not found error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeNotFoundError, match="Resource not found"):
            await api_client._request("GET", "/test")

    async def test_request_timeout_408(self, api_client, mock_session):
        """Test API request with 408 timeout."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 408
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeTimeoutError, match="Request timeout"):
            await api_client._request("GET", "/test")

    async def test_request_rate_limit(self, api_client, mock_session):
        """Test API request with rate limit error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeRateLimitError, match="Rate limit exceeded"):
            await api_client._request("GET", "/test")

    async def test_request_server_error(self, api_client, mock_session):
        """Test API request with server error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        with pytest.raises(WienerNetzeApiError, match="Server error"):
            await api_client._request("GET", "/test")

    async def test_request_connection_error(self, api_client, mock_session):
        """Test API request with connection error."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_session.request = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed")
        )

        with pytest.raises(WienerNetzeConnectionError, match="Connection error"):
            await api_client._request("GET", "/test")

    async def test_request_timeout_exception(self, api_client, mock_session):
        """Test API request with timeout exception."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_session.request = MagicMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(WienerNetzeTimeoutError, match="Request timeout"):
            await api_client._request("GET", "/test")

    async def test_get_method(self, api_client, mock_session):
        """Test GET method wrapper."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client._get("/test")

        assert result == {"data": "test"}
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"

    async def test_post_method(self, api_client, mock_session):
        """Test POST method wrapper."""
        api_client._access_token = "test_token"
        api_client._token_expires_at = datetime.now() + timedelta(hours=1)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.request = MagicMock(return_value=mock_response)

        result = await api_client._post("/test")

        assert result == {"data": "test"}
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
