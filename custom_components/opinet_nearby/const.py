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

BRAND_MAP = {
    "SKE": "SK에너지",
    "GSC": "GS칼텍스",
    "HDO": "HD현대오일뱅크",
    "SOL": "S-OIL",
    "RTE": "도로공사 알뜰",
    "RTX": "알뜰주유소",
    "NHO": "농협 알뜰",
    "ETC": "자가상표/기타",
}


def wgs84_to_katec(lon: float, lat: float) -> tuple[float, float]:
    """Convert WGS84 (lon, lat) coordinates to KATEC (x, y) coordinates for Opinet."""
    from pyproj import Transformer

    katec_proj = (
        "+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 +x_0=400000 +y_0=600000 "
        "+ellps=bessel +units=m +no_defs "
        "+towgs84=-115.80,474.99,674.11,1.16,-2.31,-1.63,6.43"
    )
    transformer = Transformer.from_crs("EPSG:4326", katec_proj, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

