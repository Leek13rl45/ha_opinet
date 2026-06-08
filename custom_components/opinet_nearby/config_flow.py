"""Config flow for opinet_nearby."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_RADIUS,
    CONF_FUEL_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_RADIUS,
    OPINET_API_URL,
    FUEL_TYPES,
    FUEL_CODES,
    RADIUS_OPTIONS,
    wgs84_to_katec,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_api_key(api_key: str, lat: float, lon: float) -> str | None:
    """Validate the API key by making a test request. Returns error string or None."""
    x, y = wgs84_to_katec(lon, lat)
    params = {
        "code": api_key,
        "x": x,
        "y": y,
        "radius": 5000,
        "prodcd": "B027",
        "sort": 1,
        "out": "json",
    }
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(OPINET_API_URL, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        # 오피넷은 에러시 RESULT 안에 에러코드 반환
                        result = data.get("RESULT", {})
                        if isinstance(result, dict) and result.get("OIL") is None and not result:
                            return "invalid_api_key"
                        return None
                    return "invalid_api_key"
    except aiohttp.ClientError:
        return "cannot_connect"
    except Exception:
        return "cannot_connect"


class OpinetNearbyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for opinet_nearby."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            lat = user_input.get(CONF_LATITUDE, self.hass.config.latitude)
            lon = user_input.get(CONF_LONGITUDE, self.hass.config.longitude)
            api_key = user_input[CONF_API_KEY]

            error = await _validate_api_key(api_key, lat, lon)
            if error:
                errors["base"] = error
            else:
                unique_id = f"{lat}_{lon}_{user_input.get(CONF_FUEL_TYPE, '휘발유')}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = user_input.get(CONF_NAME) or f"주유소 최저가 ({user_input.get(CONF_FUEL_TYPE, '휘발유')})"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_LATITUDE: lat,
                        CONF_LONGITUDE: lon,
                        CONF_RADIUS: user_input.get(CONF_RADIUS, DEFAULT_RADIUS),
                        CONF_FUEL_TYPE: user_input.get(CONF_FUEL_TYPE, "휘발유"),
                        CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        CONF_NAME: user_input.get(CONF_NAME, ""),
                    },
                )

        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
                vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS): vol.All(
                    vol.Coerce(int), vol.In(RADIUS_OPTIONS)
                ),
                vol.Optional(CONF_FUEL_TYPE, default="휘발유"): vol.In(FUEL_TYPES),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=1440)
                ),
                vol.Optional(CONF_NAME, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OpinetNearbyOptionsFlow(config_entry)


class OpinetNearbyOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_radius = self.config_entry.options.get(
            CONF_RADIUS, self.config_entry.data.get(CONF_RADIUS, DEFAULT_RADIUS)
        )
        if current_radius not in RADIUS_OPTIONS:
            current_radius = DEFAULT_RADIUS
        current_fuel = self.config_entry.options.get(
            CONF_FUEL_TYPE, self.config_entry.data.get(CONF_FUEL_TYPE, "휘발유")
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_RADIUS, default=current_radius): vol.All(
                    vol.Coerce(int), vol.In(RADIUS_OPTIONS)
                ),
                vol.Optional(CONF_FUEL_TYPE, default=current_fuel): vol.In(FUEL_TYPES),
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=1440)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
