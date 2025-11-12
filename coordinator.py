
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Concept2Client
from .const import (
    DOMAIN,
    DEFAULT_UPDATE_INTERVAL_MIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    SENSOR_DAY,
    SENSOR_LIFETIME,
    SENSOR_SEASON,
)

_LOGGER = logging.getLogger(__name__)


class Concept2Coordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        interval_min: int | None = None,
    ):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_min or DEFAULT_UPDATE_INTERVAL_MIN),
        )
        self._username = username
        self._password = password
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._client: Concept2Client | None = None
        self._attempts = 0

    async def _get_client(self) -> Concept2Client:
        session: ClientSession = async_get_clientsession(self.hass)
        if self._client is None:
            self._client = Concept2Client(session, self._username, self._password)
        return self._client

    async def _load_state(self) -> dict:
        return (await self._store.async_load()) or {}

    async def _save_state(self, state: dict) -> None:
        await self._store.async_save(state)

    async def _async_update_data(self) -> Dict[str, Any]:
        self._attempts += 1
        _LOGGER.info(
            "Concept2: nieuwe poging #%s om data op te halen op %s (interval=%s min)",
            self._attempts,
            dt_util.now().isoformat(),
            int(self.update_interval.total_seconds() / 60) if self.update_interval else 'n/a',
        )

        client = await self._get_client()
        stats = await client.fetch_stats()
        lifetime = stats.get("lifetime")
        season = stats.get("season")

        # Als site down is of parser faalt: gebruik oude waarden en gooi GEEN exception
        if lifetime is None and season is None:
            _LOGGER.warning("Concept2: Geen nieuwe stats; gebruik laatste bekende waarden.")
            state = await self._load_state()
            last_lifetime = int(state.get("lifetime", 0))
            baseline = int(state.get("baseline", last_lifetime))
            day = max(0, last_lifetime - baseline)
            last_season = int(state.get("season", 0))
            return {SENSOR_LIFETIME: last_lifetime, SENSOR_DAY: day, SENSOR_SEASON: last_season}

        # Day meters: baseline per lokale dag (HA-tijdzone)
        state = await self._load_state()
        today = dt_util.now().date().isoformat()
        last_date = state.get("date")
        baseline = state.get("baseline")

        # Gebruik vorige lifetime als deze None is, maar season niet
        if lifetime is None:
            lifetime = int(state.get("lifetime", 0))
        if season is None:
            season = int(state.get("season", 0))

        if last_date != today or baseline is None:
            state["date"] = today
            state["baseline"] = lifetime
            day = 0
        else:
            try:
                day = max(0, int(lifetime) - int(baseline))
            except Exception:
                day = 0
                state["baseline"] = lifetime

        state["lifetime"] = int(lifetime)
        state["season"] = int(season)
        await self._save_state(state)

        data = {SENSOR_LIFETIME: int(lifetime), SENSOR_DAY: day, SENSOR_SEASON: int(season)}
        _LOGGER.debug(
            "Finished fetching concept2 data (lifetime=%s, season=%s, day=%s)",
            lifetime,
            season,
            day,
        )
        return data
