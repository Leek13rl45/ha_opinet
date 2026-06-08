"""Constants for opinet_nearby."""

DOMAIN = "opinet_nearby"

CONF_API_KEY = "api_key"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_RADIUS = "radius"
CONF_FUEL_TYPE = "fuel_type"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NAME = "name"

DEFAULT_SCAN_INTERVAL = 60  # minutes
DEFAULT_RADIUS = 5  # km

OPINET_API_URL = "https://www.opinet.co.kr/api/aroundAll.do"

FUEL_TYPES = ["휘발유", "경유", "고급휘발유", "LPG"]

FUEL_CODES = {
    "휘발유": "B027",
    "경유": "D047",
    "고급휘발유": "B034",
    "LPG": "C004",
}

RADIUS_OPTIONS = [1, 3, 5]
