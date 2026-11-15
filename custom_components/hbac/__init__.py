"""HBAC: Brewfather recipes reviewed and uploaded entirely in Home Assistant."""
from datetime import timedelta
from pathlib import Path

import voluptuous as vol
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .api import BrewfatherClient, BrewfatherError
from .const import DOMAIN
from .manager import Manager

KINDS = vol.In(["recipes", "batches"])
INDEX = vol.All(int, vol.Range(min=0, max=8))
SCHEMAS = {
    "state": {},
    "catalog": {vol.Required("kind"): KINDS, vol.Optional("refresh", default=False): bool},
    "preview": {vol.Required("kind"): KINDS, vol.Required("source_id"): str,
                vol.Optional("mash_in"): vol.All(int, vol.Range(min=20, max=80)),
                vol.Optional("boil_temperature", default=103): vol.All(int, vol.Range(min=95, max=105))},
    "add": {vol.Required("preview_id"): str, vol.Required("revision"): str},
    "remove": {vol.Required("index"): INDEX, vol.Required("revision"): str},
    "move": {vol.Required("index"): INDEX, vol.Required("target"): INDEX, vol.Required("revision"): str},
    "clear": {vol.Required("revision"): str},
    "readiness": {},
    "upload": {vol.Required("revision"): str, vol.Required("replace_all"): vol.In([True])},
    "status": {},
    "acknowledge_unknown": {vol.Required("device_checked"): vol.In([True])},
}


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths([
        StaticPathConfig("/hbac/hbac-card.js", str(Path(__file__).parent / "frontend" / "hbac-card.js"), False)
    ])

    def make_handler(action):
        async def handle(call):
            managers = hass.data[DOMAIN]
            entry_id = call.data.get("entry_id")
            if entry_id is None and len(managers) == 1:
                entry_id = next(iter(managers))
            manager = managers.get(entry_id)
            if manager is None:
                raise HomeAssistantError("HBAC-Eintrag fehlt oder ist mehrdeutig. entry_id angeben.")
            try:
                return await manager.dispatch(action, call.data)
            except (BrewfatherError, ValueError) as err:
                raise HomeAssistantError(str(err)) from err
        return handle

    for action, fields in SCHEMAS.items():
        hass.services.async_register(DOMAIN, action, make_handler(action),
            schema=vol.Schema({vol.Optional("entry_id"): str, **fields}), supports_response=SupportsResponse.OPTIONAL)
    return True


async def async_setup_entry(hass, entry):
    client = BrewfatherClient(async_get_clientsession(hass), entry.data["user_id"], entry.data["api_key"])
    manager = Manager(hass, entry, client)
    await manager.load()
    hass.data[DOMAIN][entry.entry_id] = manager
    entry.async_on_unload(async_track_time_interval(hass, manager.poll, timedelta(seconds=2)))
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False


async def async_remove_entry(hass, entry):
    from homeassistant.helpers.storage import Store
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()
