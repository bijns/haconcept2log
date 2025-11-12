
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
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL_MIN, STORAGE_KEY, STORAGE_VERSION, SENSOR_DAY, SENSOR_LIFETIME, SENSOR_SEASON
_LOGGER=logging.getLogger(__name__)
class Concept2Coordinator(DataUpdateCoordinator[Dict[str,Any]]):
    def __init__(self,hass:HomeAssistant,username:str,password:str,interval_min:int|None=None):
        super().__init__(hass,_LOGGER,name=DOMAIN,update_interval=timedelta(minutes=interval_min or DEFAULT_UPDATE_INTERVAL_MIN))
        self._username=username; self._password=password
        self._store=Store(hass,STORAGE_VERSION,STORAGE_KEY)
        self._client:Concept2Client|None=None
        self._attempts=0
    async def _get_client(self)->Concept2Client:
        session:ClientSession=async_get_clientsession(self.hass)
        if self._client is None: self._client=Concept2Client(session,self._username,self._password)
        return self._client
    async def _load_state(self)->dict: return (await self._store.async_load()) or {}
    async def _save_state(self,state:dict)->None: await self._store.async_save(state)
    async def _async_update_data(self)->Dict[str,Any]:
        self._attempts+=1
        now = dt_util.now()
        _LOGGER.info("Concept2: nieuwe poging #%s om data op te halen op %s (interval=%s min)", self._attempts, now.isoformat(), int(self.update_interval.total_seconds()/60) if self.update_interval else 'n/a')
        state = await self._load_state()
        today = now.date().isoformat()
        last_date = state.get("date")
        last_lifetime = int(state.get("lifetime", 0))
        baseline = int(state.get("baseline", last_lifetime))
        last_season = int(state.get("season", 0))
        client=await self._get_client()
        stats = await client.fetch_stats()
        lifetime = stats.get("lifetime")
        season = stats.get("season")
        if last_date != today:
            new_baseline = int(lifetime) if lifetime is not None else last_lifetime
            state["date"] = today
            state["baseline"] = new_baseline
            day = 0
            state["lifetime"] = int(lifetime) if lifetime is not None else last_lifetime
            state["season"] = int(season) if season is not None else last_season
            await self._save_state(state)
            _LOGGER.info("Concept2: daggrens gedetecteerd → baseline gereset naar %s (lifetime bekend=%s)", new_baseline, lifetime is not None)
            return {SENSOR_LIFETIME: state["lifetime"], SENSOR_DAY: day, SENSOR_SEASON: state["season"]}
        if lifetime is None and season is None:
            _LOGGER.warning("Concept2: Geen nieuwe stats; gebruik laatste bekende waarden.")
            day = max(0, last_lifetime - baseline)
            return {SENSOR_LIFETIME: last_lifetime, SENSOR_DAY: day, SENSOR_SEASON: last_season}
        if lifetime is None: lifetime = last_lifetime
        if season is None: season = last_season
        try:
            day = max(0, int(lifetime) - int(baseline))
        except Exception:
            baseline = int(lifetime)
            state["baseline"] = baseline
            day = 0
        state["lifetime"] = int(lifetime)
        state["season"] = int(season)
        await self._save_state(state)
        _LOGGER.debug("Finished fetching concept2 data (lifetime=%s, season=%s, day=%s)", lifetime, season, day)
        return {SENSOR_LIFETIME: int(lifetime), SENSOR_DAY: day, SENSOR_SEASON: int(season)}
