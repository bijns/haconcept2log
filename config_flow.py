
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL_MIN, INTERVAL_MIN, INTERVAL_MAX
_INTERVAL_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=INTERVAL_MIN, max=INTERVAL_MAX))
class Concept2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input=None) -> FlowResult:
        errors={}
        if user_input is not None:
            try:
                interval = user_input.get("update_interval_min", DEFAULT_UPDATE_INTERVAL_MIN)
                interval = _INTERVAL_VALIDATOR(interval)
            except vol.Invalid:
                errors["update_interval_min"] = "invalid_interval"
            else:
                return self.async_create_entry(
                    title="Concept2 Logbook",
                    data={
                        "username": user_input["username"],
                        "password": user_input["password"],
                    },
                    options={"update_interval_min": interval},
                )
        schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Optional("update_interval_min", default=DEFAULT_UPDATE_INTERVAL_MIN): _INTERVAL_VALIDATOR,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
    async def async_step_import(self, user_input=None) -> FlowResult:
        return await self.async_step_user(user_input)
class Concept2OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry): self.config_entry=config_entry
    async def async_step_init(self, user_input=None):
        errors={}
        current=self.config_entry.options.get("update_interval_min", DEFAULT_UPDATE_INTERVAL_MIN)
        if user_input is not None:
            try:
                interval=_INTERVAL_VALIDATOR(user_input.get("update_interval_min", current))
            except vol.Invalid:
                errors["update_interval_min"]="invalid_interval"
            else:
                return self.async_create_entry(title="", data={"update_interval_min": interval})
        schema = vol.Schema({ vol.Optional("update_interval_min", default=current): _INTERVAL_VALIDATOR })
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
