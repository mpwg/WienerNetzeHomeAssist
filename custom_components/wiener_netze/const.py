"""Constants for the Wiener Netze Smart Meter integration."""

DOMAIN = "wiener_netze"

# API Configuration
API_BASE_URL = "https://api.wstw.at/gateway/WN_SMART_METER_API/1.0"
OAUTH_TOKEN_URL = "https://api.wstw.at/oauth2/token"
API_TIMEOUT = 30

# Configuration Keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_API_KEY = "api_key"
CONF_METER_POINTS = "meter_points"

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
