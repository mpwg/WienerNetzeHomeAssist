"""API client for Wiener Netze Smart Meter."""
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, TypedDict

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from .const import GRANULARITY_QUARTER_HOUR, QUALITY_VAL

_LOGGER = logging.getLogger(__name__)

# API Constants
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://api.wstw.at/oauth2/token"
DEFAULT_TIMEOUT = 30
RETRY_ATTEMPTS = 3


# Data Models
class Verbrauchsstelle(TypedDict):
    """Consumption location address information."""

    haus: str
    hausnummer1: str
    hausnummer2: str
    land: str
    ort: str
    postleitzahl: str
    stockwerk: str
    strasse: str
    strasseZusatz: str
    tuernummer: str


class Geraet(TypedDict):
    """Device/equipment information."""

    equipmentnummer: str
    geraetenummer: str


class Anlage(TypedDict):
    """Installation/facility information."""

    anlage: str
    sparte: str
    typ: str


class Idex(TypedDict):
    """IDEX smart meter interface information."""

    customerInterface: str
    displayLocked: bool
    granularity: str


class MeterPoint(TypedDict):
    """Meter point (Zählpunkt) information."""

    zaehlpunktnummer: str
    zaehlpunktname: str
    verbrauchsstelle: Verbrauchsstelle
    geraet: Geraet
    anlage: Anlage
    idex: Idex


class ConsumptionReading(TypedDict):
    """Single consumption reading (Messwert)."""

    messwert: int | float  # Consumption value
    qualitaet: str  # Quality: VAL (validated) or EST (estimated)
    zeitVon: str  # Start timestamp (ISO 8601)
    zeitBis: str  # End timestamp (ISO 8601)


class ZaehlwerkMesswerte(TypedDict):
    """Meter register measurements."""

    obisCode: str  # OBIS code
    einheit: str  # Unit (e.g., "kWh")
    messwerte: list[ConsumptionReading]


class ConsumptionData(TypedDict):
    """Consumption data response."""

    zaehlpunkt: str  # Meter point number
    zaehlwerke: list[ZaehlwerkMesswerte]


# Exception Classes
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

        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

        _LOGGER.debug("Wiener Netze API client initialized")

    @property
    def _headers(self) -> dict[str, str]:
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
    ) -> dict[str, Any]:
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
                    raise WienerNetzeApiError(
                        f"Server error: {response.status} - {text}"
                    )

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

    async def _get(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, **kwargs)

    async def _post(self, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, **kwargs)

    async def get_meter_points(self) -> list[MeterPoint]:
        """Get all meter points for the authenticated user.

        Returns:
            List of meter points with address and metadata

        Raises:
            WienerNetzeAuthError: Authentication failed
            WienerNetzeApiError: API request failed

        """
        _LOGGER.debug("Fetching meter points")

        try:
            response = await self._get("zaehlpunkte")

            # The API returns items array (or might be a list directly)
            meter_points = response.get(
                "items", response if isinstance(response, list) else []
            )

            _LOGGER.info("Retrieved %d meter point(s)", len(meter_points))

            return meter_points

        except WienerNetzeApiError:
            _LOGGER.error("Failed to fetch meter points")
            raise

    async def get_consumption_data(
        self,
        meter_point: str,
        date_from: str,
        date_to: str,
        granularity: str = GRANULARITY_QUARTER_HOUR,
    ) -> ConsumptionData:
        """Get consumption data for a meter point.

        Args:
            meter_point: Meter point number (Zählpunktnummer)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            granularity: Data granularity (QUARTER_HOUR, DAY, METER_READ)

        Returns:
            Consumption data with readings

        Raises:
            WienerNetzeNotFoundError: Meter point not found
            WienerNetzeApiError: API request failed

        """
        _LOGGER.debug(
            "Fetching consumption data for %s from %s to %s (granularity: %s)",
            meter_point,
            date_from,
            date_to,
            granularity,
        )

        endpoint = f"zaehlpunkte/{meter_point}/messwerte"
        params = {
            "datumVon": date_from,
            "datumBis": date_to,
            "wertetyp": granularity,
        }

        try:
            response = await self._get(endpoint, params=params)

            # Count total readings across all Zaehlwerke
            total_readings = sum(
                len(zw.get("messwerte", [])) for zw in response.get("zaehlwerke", [])
            )

            _LOGGER.info(
                "Retrieved %d reading(s) for meter point %s",
                total_readings,
                meter_point,
            )

            return response

        except WienerNetzeNotFoundError:
            _LOGGER.error("Meter point not found: %s", meter_point)
            raise
        except WienerNetzeApiError:
            _LOGGER.error("Failed to fetch consumption data")
            raise


def format_meter_point_address(meter_point: MeterPoint) -> str:
    """Format meter point address as string.

    Args:
        meter_point: Meter point data

    Returns:
        Formatted address string

    """
    addr = meter_point["verbrauchsstelle"]
    parts = []

    # Street and house number
    if addr.get("strasse"):
        street_part = addr["strasse"]
        if addr.get("hausnummer1"):
            street_part += f" {addr['hausnummer1']}"
        if addr.get("hausnummer2"):
            street_part += f"/{addr['hausnummer2']}"
        parts.append(street_part)

    # Additional street info
    if addr.get("strasseZusatz"):
        parts.append(addr["strasseZusatz"])

    # Floor/Staircase/Door
    floor_parts = []
    if addr.get("stockwerk"):
        floor_parts.append(f"Stockwerk {addr['stockwerk']}")
    if addr.get("haus"):
        floor_parts.append(f"Haus {addr['haus']}")
    if addr.get("tuernummer"):
        floor_parts.append(f"Tür {addr['tuernummer']}")
    if floor_parts:
        parts.append(", ".join(floor_parts))

    # Postal code and city
    if addr.get("postleitzahl") and addr.get("ort"):
        parts.append(f"{addr['postleitzahl']} {addr['ort']}")

    return ", ".join(parts)


def get_meter_point_id(meter_point: MeterPoint) -> str:
    """Get unique identifier for meter point.

    Args:
        meter_point: Meter point data

    Returns:
        Meter point number (Zählpunktnummer)

    """
    return meter_point["zaehlpunktnummer"]


# Consumption Data Helper Functions


def get_date_range_for_today() -> tuple[str, str]:
    """Get date range for today.

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    today = date.today()
    return today.isoformat(), today.isoformat()


def get_date_range_for_yesterday() -> tuple[str, str]:
    """Get date range for yesterday.

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    yesterday = date.today() - timedelta(days=1)
    return yesterday.isoformat(), yesterday.isoformat()


def get_date_range_for_last_days(days: int) -> tuple[str, str]:
    """Get date range for the last N days.

    Args:
        days: Number of days to include

    Returns:
        Tuple of (date_from, date_to) in YYYY-MM-DD format

    """
    today = date.today()
    start = today - timedelta(days=days - 1)
    return start.isoformat(), today.isoformat()


def parse_consumption_timestamp(timestamp: str) -> datetime:
    """Parse ISO 8601 timestamp from API.

    Args:
        timestamp: ISO 8601 timestamp string (e.g., "2024-11-10T00:00:00.000+01:00")

    Returns:
        Parsed datetime object

    """
    # Use fromisoformat for Python 3.11+ or handle manually
    try:
        return datetime.fromisoformat(timestamp)
    except (ValueError, AttributeError):
        # Fallback for older Python versions or complex formats
        from dateutil import parser

        return parser.isoparse(timestamp)


def calculate_total_consumption(readings: list[ConsumptionReading]) -> float:
    """Calculate total consumption from readings.

    Args:
        readings: List of consumption readings

    Returns:
        Total consumption in kWh

    """
    return sum(float(reading["messwert"]) for reading in readings)


def get_validated_readings(
    readings: list[ConsumptionReading],
) -> list[ConsumptionReading]:
    """Filter readings to only validated values.

    Args:
        readings: List of consumption readings

    Returns:
        List of validated readings (quality=VAL)

    """
    return [r for r in readings if r["qualitaet"] == QUALITY_VAL]


def extract_all_readings(consumption_data: ConsumptionData) -> list[ConsumptionReading]:
    """Extract all readings from consumption data response.

    Args:
        consumption_data: Consumption data response

    Returns:
        Flat list of all consumption readings from all Zaehlwerke

    """
    readings = []
    for zaehlwerk in consumption_data.get("zaehlwerke", []):
        readings.extend(zaehlwerk.get("messwerte", []))
    return readings
