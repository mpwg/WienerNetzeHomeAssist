# Task 08: API Client - Rate Limiting

**Category:** API Client Development
**Priority:** Medium
**Estimated Effort:** 2-3 hours
**Status:** Not Started

## Description

Implement rate limiting and request throttling for the Wiener Netze Smart Meter API to prevent hitting API limits and ensure reliable operation.

## Prerequisites

- **Task 07** completed (API Client - Consumption Data Retrieval)
- Understanding of rate limiting patterns

## Objectives

1. Implement rate limiter class
2. Add request throttling
3. Implement request queuing
4. Add rate limit headers monitoring
5. Implement backoff strategy
6. Create unit tests

## Deliverables

- [ ] `RateLimiter` class implementation
- [ ] Request queue management
- [ ] Rate limit detection from response headers
- [ ] Exponential backoff implementation
- [ ] Unit tests for rate limiting

## Implementation

### 1. Create Rate Limiter Class

Add to `api.py`:

```python
"""Rate limiter implementation."""
import asyncio
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_day: int = 1000,
    ) -> None:
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_day: Maximum requests per day

        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day

        # Sliding window for minute tracking
        self.minute_requests: deque = deque()

        # Daily counter
        self.daily_requests = 0
        self.daily_reset_time = time.time() + 86400  # 24 hours

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        Blocks until request can be made within rate limits.

        """
        async with self._lock:
            now = time.time()

            # Reset daily counter if needed
            if now >= self.daily_reset_time:
                self.daily_requests = 0
                self.daily_reset_time = now + 86400

            # Check daily limit
            if self.daily_requests >= self.requests_per_day:
                wait_time = self.daily_reset_time - now
                _LOGGER.warning(
                    "Daily rate limit reached. Waiting %.1f seconds.",
                    wait_time
                )
                await asyncio.sleep(wait_time)
                self.daily_requests = 0
                self.daily_reset_time = time.time() + 86400

            # Remove old requests from minute window
            cutoff = now - 60
            while self.minute_requests and self.minute_requests[0] < cutoff:
                self.minute_requests.popleft()

            # Check minute limit
            if len(self.minute_requests) >= self.requests_per_minute:
                oldest = self.minute_requests[0]
                wait_time = 60 - (now - oldest)
                _LOGGER.debug(
                    "Rate limit approaching. Waiting %.1f seconds.",
                    wait_time
                )
                await asyncio.sleep(wait_time)

                # Remove old requests again
                cutoff = time.time() - 60
                while self.minute_requests and self.minute_requests[0] < cutoff:
                    self.minute_requests.popleft()

            # Record this request
            self.minute_requests.append(time.time())
            self.daily_requests += 1

    def update_from_headers(self, headers: dict) -> None:
        """Update rate limit info from response headers.

        Args:
            headers: Response headers from API

        """
        # Check for rate limit headers
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        if "X-RateLimit-Remaining" in headers:
            remaining = int(headers["X-RateLimit-Remaining"])
            if remaining < 10:
                _LOGGER.warning(
                    "API rate limit low: %d requests remaining",
                    remaining
                )

        if "Retry-After" in headers:
            retry_after = int(headers["Retry-After"])
            _LOGGER.warning(
                "API requested retry after %d seconds",
                retry_after
            )

    @property
    def stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary with rate limit stats

        """
        now = time.time()
        cutoff = now - 60

        # Count recent requests
        recent = sum(1 for t in self.minute_requests if t > cutoff)

        return {
            "requests_last_minute": recent,
            "requests_today": self.daily_requests,
            "minute_limit": self.requests_per_minute,
            "daily_limit": self.requests_per_day,
            "daily_reset_in": max(0, self.daily_reset_time - now),
        }
```

### 2. Update API Client to Use Rate Limiter

```python
class WienerNetzeApiClient:
    """API client with rate limiting."""

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

        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            requests_per_minute=60,  # Conservative estimate
            requests_per_day=1000,   # Conservative estimate
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Make API request with rate limiting.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Response data

        Raises:
            WienerNetzeApiError: API request failed

        """
        # Acquire rate limit permission
        await self._rate_limiter.acquire()

        # Ensure we have valid token
        await self._ensure_authenticated()

        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "x-Gateway-APIKey": self._api_key,
            "Accept": "application/json",
        }

        try:
            async with self._session.request(
                method, url, headers=headers, **kwargs
            ) as response:
                # Update rate limiter from response headers
                self._rate_limiter.update_from_headers(response.headers)

                if response.status == 429:
                    # Rate limit hit
                    retry_after = response.headers.get("Retry-After", "60")
                    raise WienerNetzeRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after}s"
                    )

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientResponseError as err:
            if err.status == 429:
                raise WienerNetzeRateLimitError(str(err)) from err
            raise WienerNetzeApiError(str(err)) from err
```

### 3. Add Rate Limit Exception

```python
class WienerNetzeRateLimitError(WienerNetzeApiError):
    """Rate limit exceeded error."""
    pass
```

### 4. Create Unit Tests

Add to `tests/test_rate_limiting.py`:

```python
"""Tests for rate limiting."""
import asyncio
import pytest
import time

from custom_components.wiener_netze.api import RateLimiter


async def test_rate_limiter_basic():
    """Test basic rate limiting."""
    limiter = RateLimiter(requests_per_minute=5, requests_per_day=100)

    # Should allow 5 requests quickly
    for _ in range(5):
        await limiter.acquire()

    # 6th request should be delayed
    start = time.time()
    await limiter.acquire()
    elapsed = time.time() - start

    # Should have waited at least 1 second
    assert elapsed >= 1.0


async def test_rate_limiter_stats():
    """Test rate limiter statistics."""
    limiter = RateLimiter(requests_per_minute=10, requests_per_day=100)

    # Make some requests
    for _ in range(3):
        await limiter.acquire()

    stats = limiter.stats
    assert stats["requests_last_minute"] == 3
    assert stats["requests_today"] == 3
    assert stats["minute_limit"] == 10
    assert stats["daily_limit"] == 100


async def test_rate_limiter_daily_reset():
    """Test daily counter reset."""
    limiter = RateLimiter(requests_per_minute=100, requests_per_day=5)

    # Use up daily quota
    for _ in range(5):
        await limiter.acquire()

    # Force reset by setting reset time to now
    limiter.daily_reset_time = time.time()

    # Should allow more requests after reset
    await limiter.acquire()
    assert limiter.daily_requests == 1


async def test_update_from_headers():
    """Test updating from response headers."""
    limiter = RateLimiter()

    # Test with rate limit headers
    headers = {
        "X-RateLimit-Remaining": "5",
        "X-RateLimit-Limit": "60",
    }

    # Should log warning but not raise
    limiter.update_from_headers(headers)

    # Test with retry-after
    headers = {"Retry-After": "30"}
    limiter.update_from_headers(headers)
```

## Acceptance Criteria

- [ ] Rate limiter class implemented
- [ ] Request throttling works correctly
- [ ] Minute and daily limits enforced
- [ ] Rate limit headers monitored
- [ ] 429 status code handled properly
- [ ] Statistics available for monitoring
- [ ] All tests passing
- [ ] Integration with API client complete

## Testing

```bash
# Run rate limiting tests
pytest tests/test_rate_limiting.py -v

# Test with API client
pytest tests/test_api.py -v -k rate

# Performance test (manual)
python -c "
import asyncio
from custom_components.wiener_netze.api import RateLimiter

async def test():
    limiter = RateLimiter(requests_per_minute=10)
    for i in range(15):
        await limiter.acquire()
        print(f'Request {i+1}', limiter.stats)

asyncio.run(test())
"
```

## References

- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [HTTP Status 429](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429)

## Notes

- Use conservative rate limits until actual limits are known
- Monitor rate limit headers from API responses
- Implement exponential backoff for repeated rate limit hits
- Log rate limit warnings for debugging
- Consider making limits configurable
- Track statistics for monitoring and optimization
- Handle both per-minute and per-day limits
- Use asyncio.Lock for thread safety

## Next Task

→ **Task 09:** API Client - Error Handling & Retry Logic
