
from __future__ import annotations
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.diagnostics import async_redact_data
from .const import DOMAIN
TO_REDACT = {"username", "password"}
async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("coordinator")
    diag = {"config_entry": async_redact_data({"title": entry.title, "entry_id": entry.entry_id, "version": entry.version, "data": dict(entry.data), "options": dict(entry.options)}, TO_REDACT)}
    if coordinator is not None:
        try: state = await coordinator._store.async_load()
        except Exception: state = None
        diag["coordinator"] = {
            "update_interval_sec": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
            "attempts": getattr(coordinator, "_attempts", None),
            "last_update_success": coordinator.last_update_success,
            "data": coordinator.data,
        }
        diag["storage_state"] = state
    return diag
