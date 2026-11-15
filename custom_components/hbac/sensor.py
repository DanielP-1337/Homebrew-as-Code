"""Upload status for HA dashboards and automations."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([UploadSensor(hass.data[DOMAIN][entry.entry_id])])


class UploadSensor(SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:beer"
    _attr_has_entity_name = True
    _attr_name = "Upload"

    def __init__(self, manager):
        self.manager = manager
        self._attr_unique_id = manager.entry.entry_id + "_upload"
        self._attr_device_info = {"identifiers": {(DOMAIN, manager.entry.entry_id)},
                                  "name": manager.entry.title, "manufacturer": "HBAC", "model": "Brewfather → Braumeister"}

    @property
    def native_value(self):
        return (self.manager.job or {}).get("result", "idle")

    @property
    def extra_state_attributes(self):
        job = self.manager.job or {}
        return {"entry_id": self.manager.entry.entry_id, "queued_recipes": len(self.manager.queue),
                "job_id": job.get("job_id"), "written": job.get("written"),
                "content_verification": job.get("content_verification", "not_available"),
                "error": self.manager.error}

    async def async_added_to_hass(self):
        self.async_on_remove(async_dispatcher_connect(self.hass, self.manager.signal, self.async_write_ha_state))
