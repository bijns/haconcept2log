
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_DAY, SENSOR_LIFETIME, SENSOR_SEASON
from .coordinator import Concept2Coordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: Concept2Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        Concept2LifetimeSensor(coordinator, entry.entry_id),
        Concept2DaySensor(coordinator, entry.entry_id),
        Concept2SeasonSensor(coordinator, entry.entry_id),
    ])


class _Concept2BaseSensor(CoordinatorEntity[Concept2Coordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "m"

    def __init__(self, coordinator: Concept2Coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "concept2_logbook")},
            "name": "Concept2 Logbook",
            "manufacturer": "Concept2",
            "model": "Logbook",
            "configuration_url": "https://log.concept2.com",
        }


class Concept2LifetimeSensor(_Concept2BaseSensor):
    def __init__(self, coordinator: Concept2Coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_name = "Concept2 Lifetime Meters"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{SENSOR_LIFETIME}"
        self._icon = "mdi:tape-measure"

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        val = data.get(SENSOR_LIFETIME)
        return int(val) if val is not None else None


class Concept2DaySensor(_Concept2BaseSensor):
    def __init__(self, coordinator: Concept2Coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_name = "Concept2 Day Meters"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{SENSOR_DAY}"
        self._icon = "mdi:rowing"

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        val = data.get(SENSOR_DAY)
        return int(val) if val is not None else None


class Concept2SeasonSensor(_Concept2BaseSensor):
    def __init__(self, coordinator: Concept2Coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_name = "Concept2 Season Meters"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{SENSOR_SEASON}"
        self._icon = "mdi:calendar-range"

    @property
    def icon(self) -> str | None:
        return self._icon

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        val = data.get(SENSOR_SEASON)
        return int(val) if val is not None else None
