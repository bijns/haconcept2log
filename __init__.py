
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from .const import DOMAIN
from .coordinator import Concept2Coordinator
from .config_flow import Concept2OptionsFlowHandler
PLATFORMS=[Platform.SENSOR]
async def async_setup_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    username=entry.data["username"]; password=entry.data["password"]
    interval=entry.options.get("update_interval_min", entry.data.get("update_interval_min"))
    coordinator=Concept2Coordinator(hass,username,password,interval)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN,{})[entry.entry_id]={"coordinator":coordinator}
    await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS)
    return True
async def async_unload_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    unload_ok=await hass.config_entries.async_unload_platforms(entry,PLATFORMS)
    if unload_ok: hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
async def async_get_options_flow(config_entry:ConfigEntry)->OptionsFlow:
    return Concept2OptionsFlowHandler(config_entry)
