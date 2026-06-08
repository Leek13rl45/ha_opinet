"""Sensor platform for opinet_nearby."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import OpinetCoordinator
from .const import DOMAIN, CONF_NAME, CONF_FUEL_TYPE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[OpinetCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from config entry."""
    coordinator = entry.runtime_data

    base_name = entry.data.get(CONF_NAME, "") or f"주유소 최저가"

    async_add_entities(
        [
            OpinetStationSensor(coordinator, entry, rank=1, base_name=base_name),
            OpinetStationSensor(coordinator, entry, rank=2, base_name=base_name),
        ]
    )


class OpinetStationSensor(CoordinatorEntity[OpinetCoordinator], SensorEntity):
    """Sensor representing a ranked cheapest gas station."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "KRW/L"
    _attr_icon = "mdi:gas-station"

    def __init__(
        self,
        coordinator: OpinetCoordinator,
        entry: ConfigEntry[OpinetCoordinator],
        rank: int,
        base_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._rank = rank
        self._entry = entry
        self._base_name = base_name
        self._attr_unique_id = f"{entry.entry_id}_rank{rank}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        data = self.coordinator.data
        if data:
            station = data.get(f"rank{self._rank}")
            if station and station.get("name"):
                return f"{self._rank}위 ({station['name']})"
        return f"{self._rank}위"

    @property
    def device_info(self) -> DeviceInfo:
        fuel = self._entry.data.get(CONF_FUEL_TYPE, "휘발유")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._base_name,
            manufacturer="한국석유공사 오피넷",
            model=f"{fuel} 최저가 탐색",
        )

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        key = f"rank{self._rank}"
        return (
            self.coordinator.data is not None
            and self.coordinator.data.get(key) is not None
        )

    @property
    def native_value(self) -> int | None:
        """Return the gas price as the state."""
        data = self.coordinator.data
        if not data:
            return None
        station = data.get(f"rank{self._rank}")
        if not station:
            return None
        return int(station["price"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return station details as attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        station = data.get(f"rank{self._rank}")
        if not station:
            return {}

        fuel_type = data.get("fuel_type", "")
        radius = data.get("radius", "")

        return {
            "station_name": station["name"],
            "주유소명": station["name"],
            "price": station["price"],
            "가격": f"{int(station['price']):,}원/L",
            "distance": station["distance"],
            "거리": f"{station['distance']}km",
            "address": station["address"],
            "주소": station["address"],
            "brand": station["brand"],
            "브랜드": station["brand"],
            "self_service": station["self"],
            "셀프여부": "셀프" if station["self"] else "일반",
            "fuel_type": fuel_type,
            "연료종류": fuel_type,
            "search_radius": radius,
            "검색반경": f"{radius}km",
            "rank": self._rank,
            "순위": f"{self._rank}위",
        }
