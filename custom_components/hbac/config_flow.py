"""UI setup with private credentials and a selected Braumeister entry."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import BrewfatherAuthError, BrewfatherClient, BrewfatherError
from .const import BRIDGE_DOMAIN, DOMAIN


class HbacConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        entries = {entry.entry_id: entry.title for entry in self.hass.config_entries.async_entries(BRIDGE_DOMAIN)}
        if not entries:
            return self.async_abort(reason="no_bridge")
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input["bridge_entry_id"])
            self._abort_if_unique_id_configured()
            client = BrewfatherClient(async_get_clientsession(self.hass), user_input["user_id"], user_input["api_key"])
            try:
                await client.get("recipes", limit=1)
                await client.get("batches", limit=1)
            except BrewfatherAuthError:
                errors["base"] = "invalid_auth"
            except BrewfatherError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="HBAC · " + entries[user_input["bridge_entry_id"]], data=user_input)
        return self.async_show_form(step_id="user", errors=errors, data_schema=vol.Schema({
            vol.Required("user_id"): str,
            vol.Required("api_key"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required("bridge_entry_id"): vol.In(entries),
        }))

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            client = BrewfatherClient(async_get_clientsession(self.hass), user_input["user_id"], user_input["api_key"])
            try:
                await client.get("recipes", limit=1)
                await client.get("batches", limit=1)
            except BrewfatherAuthError:
                errors["base"] = "invalid_auth"
            except BrewfatherError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(step_id="reconfigure", errors=errors, data_schema=vol.Schema({
            vol.Required("user_id", default=entry.data["user_id"]): str,
            vol.Required("api_key"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
        }))
