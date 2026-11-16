"""Optional recipe providers; BeerXML-only setup requires no cloud account."""
from pathlib import Path

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import BrewfatherAuthError, BrewfatherClient, BrewfatherError
from .brewersfriend import BrewersFriendClient
from .const import BRIDGE_DOMAIN, DOMAIN


class HbacConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def validate(self, data):
        if bool(data.get("user_id")) != bool(data.get("api_key")):
            return {"base": "incomplete_brewfather"}
        directory = data.get("import_directory", "")
        if directory and not Path(directory).is_absolute():
            return {"base": "invalid_directory"}
        session = async_get_clientsession(self.hass)
        try:
            if data.get("user_id"):
                client = BrewfatherClient(session, data["user_id"], data["api_key"])
                await client.get("recipes", limit=1)
                await client.get("batches", limit=1)
            if data.get("brewersfriend_api_key"):
                await BrewersFriendClient(session, data["brewersfriend_api_key"]).page(limit=1)
        except BrewfatherAuthError:
            return {"base": "invalid_auth"}
        except BrewfatherError:
            return {"base": "cannot_connect"}
        return {}

    def fields(self, current=None):
        current = current or {}
        return {
            vol.Optional("user_id", default=current.get("user_id", "")): str,
            vol.Optional("api_key", default=current.get("api_key", "")): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional("brewersfriend_api_key", default=current.get("brewersfriend_api_key", "")): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional("import_directory", default=current.get("import_directory", self.hass.config.path("hbac", "import"))): str,
        }

    async def async_step_user(self, user_input=None):
        entries = {entry.entry_id: entry.title for entry in self.hass.config_entries.async_entries(BRIDGE_DOMAIN)}
        if not entries:
            return self.async_abort(reason="no_bridge")
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input["bridge_entry_id"])
            self._abort_if_unique_id_configured()
            errors = await self.validate(user_input)
            if not errors:
                return self.async_create_entry(title="HBAC · " + entries[user_input["bridge_entry_id"]], data=user_input)
        return self.async_show_form(step_id="user", errors=errors, data_schema=vol.Schema({
            **self.fields(user_input), vol.Required("bridge_entry_id"): vol.In(entries),
        }))

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            errors = await self.validate(user_input)
            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(step_id="reconfigure", errors=errors,
                                    data_schema=vol.Schema(self.fields(user_input or entry.data)))
