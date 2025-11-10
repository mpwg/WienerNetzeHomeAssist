# Task 09: API Client - Error Handling & Retry Logic

**Category:** API Client Development
**Priority:** High
**Estimated Effort:** 3-4 hours
**Status:** Not Started

## Description

Implement comprehensive error handling and retry logic for the Wiener Netze Smart Meter API client to ensure reliability and resilience.

## Prerequisites

- **Task 08** completed (API Client - Rate Limiting)
- Understanding of retry patterns and exponential backoff

## Objectives

1. Implement comprehensive error handling
2. Add retry logic with exponential backoff
3. Handle transient vs permanent errors
4. Implement circuit breaker pattern
5. Add detailed error logging
6. Create unit tests

## Deliverables

- [ ] Error classification system
- [ ] Retry decorator with exponential backoff
- [ ] Circuit breaker implementation
- [ ] Comprehensive error messages
- [ ] Error recovery strategies
- [ ] Unit tests for error scenarios

## Implementation

### 1. Define Error Hierarchy

Update `api.py` with comprehensive error classes:

```python
"""API error classes."""


class WienerNetzeError(Exception):
    """Base exception for Wiener Netze integration."""
    pass


class WienerNetzeApiError(WienerNetzeError):
    """General API error."""
    pass


class WienerNetzeAuthError(WienerNetzeApiError):
    """Authentication error."""
    pass


class WienerNetzeConnectionError(WienerNetzeApiError):
    """Connection error."""
    pass


class WienerNetzeRateLimitError(WienerNetzeApiError):
    """Rate limit exceeded error."""
    pass


class WienerNetzeTimeoutError(WienerNetzeApiError):
    """Request timeout error."""
    pass


class WienerNetzeNotFoundError(WienerNetzeApiError):
    """Resource not found error."""
    pass


class WienerNetzeForbiddenError(WienerNetzeApiError):
    """Access forbidden error."""
    pass


class WienerNetzeServerError(WienerNetzeApiError):
    """Server error (5xx)."""
    pass
```

### 2. Implement Retry Decorator

```python
"""Retry decorator with exponential backoff."""
import functools
import random
from typing import Callable, Type


def retry_on_error(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on: tuple[Type[Exception], ...] = (
        WienerNetzeConnectionError,
        WienerNetzeTimeoutError,
        WienerNetzeServerError,
    ),
    reraise_on: tuple[Type[Exception], ...] = (
        WienerNetzeAuthError,
        WienerNetzeForbiddenError,
        WienerNetzeNotFoundError,
    ),
):
    """Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff delay
        retry_on: Exceptions that trigger retry
        reraise_on: Exceptions that should not be retried

    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except reraise_on as err:
                    # Don't retry these errors
                    _LOGGER.error(
                        "%s failed with non-retryable error: %s",
                        func.__name__, err
                    )
                    raise

                except retry_on as err:
                    last_exception = err

                    if attempt < max_retries:
                        # Calculate backoff with jitter
                        delay = (backoff_factor ** attempt) + random.uniform(0, 1)

                        _LOGGER.warning(
                            "%s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                            func.__name__, attempt + 1, max_retries, err, delay
                        )

                        await asyncio.sleep(delay)
                    else:
                        _LOGGER.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_retries + 1, err
                        )

                except Exception as err:
                    # Unexpected error
                    _LOGGER.exception(
                        "%s failed with unexpected error: %s",
                        func.__name__, err
                    )
                    raise

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator
```

### 3. Implement Circuit Breaker

```python
"""Circuit breaker pattern implementation."""
import enum
from datetime import datetime, timedelta


class CircuitState(enum.Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker for API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = WienerNetzeApiError,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to track

        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        if self._state == CircuitState.OPEN:
            # Check if we should try recovery
            if (
                self._last_failure_time
                and datetime.now() - self._last_failure_time
                > timedelta(seconds=self.recovery_timeout)
            ):
                self._state = CircuitState.HALF_OPEN
                _LOGGER.info("Circuit breaker entering half-open state")

        return self._state

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            WienerNetzeApiError: If circuit is open

        """
        if self.state == CircuitState.OPEN:
            raise WienerNetzeApiError(
                f"Circuit breaker is open. "
                f"Will retry after {self.recovery_timeout}s"
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as err:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            _LOGGER.info("Circuit breaker closing after successful call")

        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._failure_count >= self.failure_threshold:
            _LOGGER.warning(
                "Circuit breaker opening after %d failures",
                self._failure_count
            )
            self._state = CircuitState.OPEN
```

### 4. Update API Client with Error Handling

```python
class WienerNetzeApiClient:
    """API client with comprehensive error handling."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        api_key: str,
    ) -> None:
        """Initialize API client."""
        self._session = session
        self._client_id = client_id
        self._client_secret = client_secret
        self._api_key = api_key
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        self._rate_limiter = RateLimiter()
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
        )

    @retry_on_error(max_retries=3)
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Make API request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Response data

        Raises:
            WienerNetzeApiError: API request failed

        """
        # Use circuit breaker
        return await self._circuit_breaker.call(
            self._do_request, method, endpoint, **kwargs
        )

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Execute HTTP request.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Response data

        """
        # Rate limiting
        await self._rate_limiter.acquire()

        # Ensure authenticated
        await self._ensure_authenticated()

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "x-Gateway-APIKey": self._api_key,
            "Accept": "application/json",
        }

        try:
            async with self._session.request(
                method, url, headers=headers, timeout=30, **kwargs
            ) as response:
                # Update rate limiter
                self._rate_limiter.update_from_headers(response.headers)

                # Handle specific status codes
                if response.status == 400:
                    text = await response.text()
                    raise WienerNetzeApiError(f"Bad request: {text}")

                elif response.status == 401:
                    # Token might be invalid, clear it
                    self._access_token = None
                    raise WienerNetzeAuthError("Authentication failed")

                elif response.status == 403:
                    raise WienerNetzeForbiddenError(
                        "Access forbidden. Check API permissions."
                    )

                elif response.status == 404:
                    raise WienerNetzeNotFoundError(
                        f"Resource not found: {endpoint}"
                    )

                elif response.status == 408:
                    raise WienerNetzeTimeoutError("Request timeout")

                elif response.status == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise WienerNetzeRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s"
                    )

                elif response.status >= 500:
                    text = await response.text()
                    raise WienerNetzeServerError(
                        f"Server error ({response.status}): {text}"
                    )

                response.raise_for_status()
                return await response.json()

        except asyncio.TimeoutError as err:
            raise WienerNetzeTimeoutError("Request timed out") from err

        except aiohttp.ClientConnectionError as err:
            raise WienerNetzeConnectionError(
                f"Connection failed: {err}"
            ) from err

        except aiohttp.ClientError as err:
            raise WienerNetzeApiError(f"Client error: {err}") from err
```

### 5. Create Unit Tests

Add to `tests/test_error_handling.py`:

```python
"""Tests for error handling."""
import pytest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientError, ClientResponseError

from custom_components.wiener_netze.api import (
    WienerNetzeApiClient,
    WienerNetzeAuthError,
    WienerNetzeConnectionError,
    WienerNetzeTimeoutError,
    retry_on_error,
    CircuitBreaker,
)


async def test_retry_decorator_success():
    """Test retry decorator with successful call."""
    call_count = 0

    @retry_on_error(max_retries=3)
    async def test_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await test_func()
    assert result == "success"
    assert call_count == 1


async def test_retry_decorator_eventual_success():
    """Test retry decorator with eventual success."""
    call_count = 0

    @retry_on_error(max_retries=3)
    async def test_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise WienerNetzeConnectionError("Failed")
        return "success"

    result = await test_func()
    assert result == "success"
    assert call_count == 3


async def test_retry_decorator_max_retries():
    """Test retry decorator exhausts retries."""
    @retry_on_error(max_retries=2)
    async def test_func():
        raise WienerNetzeConnectionError("Always fails")

    with pytest.raises(WienerNetzeConnectionError):
        await test_func()


async def test_retry_decorator_non_retryable():
    """Test retry decorator with non-retryable error."""
    call_count = 0

    @retry_on_error(max_retries=3)
    async def test_func():
        nonlocal call_count
        call_count += 1
        raise WienerNetzeAuthError("Auth failed")

    with pytest.raises(WienerNetzeAuthError):
        await test_func()

    # Should not retry auth errors
    assert call_count == 1


async def test_circuit_breaker_opens():
    """Test circuit breaker opens after failures."""
    breaker = CircuitBreaker(failure_threshold=3)

    async def failing_func():
        raise WienerNetzeApiError("Failed")

    # Cause failures
    for _ in range(3):
        with pytest.raises(WienerNetzeApiError):
            await breaker.call(failing_func)

    # Circuit should be open
    assert breaker.state.value == "open"

    # Further calls should fail immediately
    with pytest.raises(WienerNetzeApiError, match="Circuit breaker is open"):
        await breaker.call(failing_func)


async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery."""
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=0,  # Immediate recovery for testing
    )

    async def func(should_fail: bool):
        if should_fail:
            raise WienerNetzeApiError("Failed")
        return "success"

    # Open circuit
    for _ in range(2):
        with pytest.raises(WienerNetzeApiError):
            await breaker.call(func, True)

    # Should enter half-open
    assert breaker.state.value == "half_open"

    # Successful call should close circuit
    result = await breaker.call(func, False)
    assert result == "success"
    assert breaker.state.value == "closed"
```

## Acceptance Criteria

- [ ] Comprehensive error hierarchy defined
- [ ] Retry logic with exponential backoff implemented
- [ ] Circuit breaker pattern implemented
- [ ] Transient errors retried automatically
- [ ] Permanent errors fail immediately
- [ ] Detailed error logging in place
- [ ] All HTTP status codes handled
- [ ] All tests passing
- [ ] Error messages are user-friendly

## Testing

```bash
# Run error handling tests
pytest tests/test_error_handling.py -v

# Test retry logic
pytest tests/test_error_handling.py::test_retry -v

# Test circuit breaker
pytest tests/test_error_handling.py::test_circuit -v

# Integration test with API
pytest tests/test_api.py -v
```

## References

- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Notes

- Distinguish between retryable and non-retryable errors
- Use exponential backoff with jitter to avoid thundering herd
- Circuit breaker prevents cascading failures
- Log all errors with appropriate severity
- Provide user-friendly error messages
- Consider timeout configuration
- Handle network errors gracefully
- Test error scenarios thoroughly

## Next Task

→ **Task 10:** Integration Initialization (**init**.py)
