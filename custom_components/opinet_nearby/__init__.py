"""오피넷 주변 최저가 주유소 Custom Component."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_FUEL_TYPE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    OPINET_API_URL,
    FUEL_CODES,
    wgs84_to_katec,
    BRAND_MAP,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up opinet_nearby from a config entry."""
    coordinator = OpinetCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class OpinetCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from Opinet API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )
        self.entry = entry

    async def _async_update_data(self):
        """Fetch data from Opinet."""
        try:
            api_key = self.entry.data[CONF_API_KEY]
            lat = self.entry.data[CONF_LATITUDE]
            lon = self.entry.data[CONF_LONGITUDE]
            try:
                radius = int(self.entry.options.get(
                    CONF_RADIUS, self.entry.data.get(CONF_RADIUS, 5)
                ))
            except (ValueError, TypeError):
                radius = 5
            fuel_type = self.entry.options.get(
                CONF_FUEL_TYPE, self.entry.data.get(CONF_FUEL_TYPE, "휘발유")
            )
            prod_cd = FUEL_CODES.get(fuel_type, "B027")

            x, y = wgs84_to_katec(lon, lat)
            _LOGGER.warning(
                "오피넷 API 호출 좌표 정보 - 입력 위경도: (%s, %s), 변환 KATEC: (%s, %s), 반경: %s km",
                lat, lon, x, y, radius
            )

            params = {
                "code": api_key,
                "x": x,
                "y": y,
                "radius": radius * 1000,  # meters
                "prodcd": prod_cd,
                "sort": 1,  # 가격순 정렬
                "out": "json",
            }

            try:
                async with async_timeout.timeout(10):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(OPINET_API_URL, params=params) as resp:
                            if resp.status != 200:
                                raise UpdateFailed(f"HTTP {resp.status}")
                            data = await resp.json(content_type=None)
                            _LOGGER.warning("오피넷 API 원시 응답 데이터: %s", data)
            except aiohttp.ClientError as err:
                raise UpdateFailed(f"연결 오류: {err}") from err
            except Exception as err:
                raise UpdateFailed(f"데이터 조회 실패: {err}") from err

            stations = []
            try:
                oil_list = data.get("RESULT", {}).get("OIL", [])
                for item in oil_list:
                    price_str = item.get("PRICE", "0")
                    try:
                        price = int(float(price_str))
                    except (ValueError, TypeError):
                        price = 0

                    dist_str = item.get("DISTANCE", "0")
                    try:
                        distance = float(dist_str)
                    except (ValueError, TypeError):
                        distance = 0.0

                    brand_cd = item.get("POLL_DIV_CD", "")
                    brand_nm = BRAND_MAP.get(brand_cd, "기타")

                    stations.append(
                        {
                            "name": item.get("OS_NM", "알 수 없음"),
                            "price": price,
                            "distance": round(distance / 1000, 2),  # km
                            "address": item.get("VAN_ADR", ""),
                            "brand": brand_nm,
                            "id": item.get("UNI_ID", ""),
                            "self": item.get("SELF_YN", "N") == "Y",
                        }
                    )
            except Exception as err:
                raise UpdateFailed(f"데이터 파싱 오류: {err}") from err

            if not stations:
                _LOGGER.warning("반경 %skm 내 주유소를 찾을 수 없습니다.", radius)

            # 가격순 정렬 후 top 2
            stations.sort(key=lambda x: x["price"])
            return {
                "stations": stations[:10],
                "rank1": stations[0] if len(stations) > 0 else None,
                "rank2": stations[1] if len(stations) > 1 else None,
                "fuel_type": fuel_type,
                "radius": radius,
            }
        except Exception as err:
            _LOGGER.error("오피넷 데이터 업데이트 중 에러 발생: %s", err, exc_info=True)
            if not isinstance(err, UpdateFailed):
                raise UpdateFailed(f"업데이트 에러: {err}") from err
            raise
