"""Persistent review queue and conservative upload lifecycle."""
import asyncio
import time
from copy import deepcopy
from uuid import uuid4

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .api import BrewfatherError
from .const import ACTIVE, BRIDGE_DOMAIN, DOMAIN
from .converter import convert


class Manager:
    def __init__(self, hass, entry, client):
        self.hass, self.entry, self.client = hass, entry, client
        self.store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self.lock = asyncio.Lock()
        self.queue = []
        self.revision = uuid4().hex
        self.job = None
        self.readiness = None
        self.previews = {}
        self.catalogs = {}
        self.error = None

    @property
    def signal(self):
        return f"{DOMAIN}_{self.entry.entry_id}"

    async def load(self):
        data = await self.store.async_load() or {}
        self.queue = data.get("queue", [])
        self.revision = data.get("revision", self.revision)
        self.job = data.get("job")
        if self.job and self.job.get("result") == "submitting":
            self.job["result"] = "outcome_unknown"
            await self.save()

    async def save(self):
        await self.store.async_save({"queue": self.queue, "revision": self.revision, "job": self.job})
        self.notify()

    def notify(self):
        async_dispatcher_send(self.hass, self.signal)

    def state(self):
        queue = [{k: deepcopy(v) for k, v in item.items() if k != "source_recipe"} for item in self.queue]
        return {"entry_id": self.entry.entry_id, "queue": queue, "revision": self.revision,
                "job": deepcopy(self.job), "readiness": deepcopy(self.readiness), "error": self.error}

    async def bridge(self, action, data=None):
        if not self.hass.services.has_service(BRIDGE_DOMAIN, action):
            raise HomeAssistantError("Bridge-Aktionen aus PR #30 fehlen. HA-Integration und Bridge aktualisieren.")
        result = await self.hass.services.async_call(
            BRIDGE_DOMAIN, action,
            {"config_entry_id": self.entry.data["bridge_entry_id"], **(data or {})},
            blocking=True, return_response=True,
        )
        if not isinstance(result, dict):
            raise HomeAssistantError("Ungültige Bridge-Antwort.")
        return result

    def editable(self):
        if self.job and self.job.get("result") in ACTIVE:
            raise HomeAssistantError("Upload läuft oder Ausgang ist unklar. Erst den Auftrag prüfen.")

    async def dispatch(self, action, data):
        async with self.lock:
            if action != "state":
                self.error = None
            try:
                return await self._dispatch(action, data)
            except (HomeAssistantError, ValueError, BrewfatherError) as err:
                self.error = str(err)
                self.notify()
                raise

    async def _dispatch(self, action, data):
        if action == "state":
            return self.state()
        if action == "catalog":
            kind = data["kind"]
            cached = self.catalogs.get(kind)
            if not cached or data.get("refresh") or time.monotonic() - cached[0] > 300:
                items = await self.client.catalog(kind)
                self.catalogs[kind] = (time.monotonic(), items)
            return {"items": self.catalogs[kind][1]}
        if action == "preview":
            source = await self.client.get(data["kind"], data["source_id"])
            preview = convert(source, data["kind"], data["source_id"], data.get("mash_in"), data.get("boil_temperature", 103))
            token = uuid4().hex
            self.previews[token] = preview
            while len(self.previews) > 20:
                del self.previews[next(iter(self.previews))]
            return {"preview_id": token, **{k: v for k, v in preview.items() if k != "source_recipe"}}
        if action in ("add", "remove", "move", "clear"):
            self.editable()
            if data["revision"] != self.revision:
                raise HomeAssistantError("Die Liste wurde geändert. Ansicht aktualisieren.")
            if action == "add":
                if len(self.queue) >= 9:
                    raise HomeAssistantError("Maximal neun Geräteplätze.")
                preview = self.previews.get(data["preview_id"])
                if not preview:
                    raise HomeAssistantError("Vorschau abgelaufen. Rezept erneut prüfen.")
                if any(item["program"]["name"] == preview["program"]["name"] for item in self.queue):
                    raise HomeAssistantError("Der gekürzte Gerätename ist bereits in der Liste vorhanden.")
                self.queue.append(deepcopy(preview))
            elif action == "clear":
                self.queue = []
            else:
                index = data["index"]
                if not 0 <= index < len(self.queue):
                    raise HomeAssistantError("Unbekannter Listenplatz.")
                if action == "remove":
                    self.queue.pop(index)
                else:
                    target = data["target"]
                    if not 0 <= target < len(self.queue):
                        raise HomeAssistantError("Ungültiger Zielplatz.")
                    self.queue.insert(target, self.queue.pop(index))
            self.revision = uuid4().hex
            await self.save()
            return self.state()
        if action == "readiness":
            self.readiness = await self.bridge("recipe_upload_readiness")
            self.notify()
            return self.state()
        if action == "upload":
            self.editable()
            if data.get("replace_all") is not True or data["revision"] != self.revision:
                raise HomeAssistantError("Aktuelle Liste prüfen und das Ersetzen aller Geräteplätze bestätigen.")
            if not 1 <= len(self.queue) <= 9:
                raise HomeAssistantError("Die Upload-Liste muss 1 bis 9 Rezepte enthalten.")
            self.readiness = await self.bridge("recipe_upload_readiness")
            if self.readiness.get("ready_for_upload") is not True:
                raise HomeAssistantError("Gerät nicht bereit: " + ", ".join(self.readiness.get("blocking_reasons", [])))
            self.job = {"result": "submitting", "started_at": time.time(), "revision": self.revision,
                        "programs": [deepcopy(item["program"]) for item in self.queue]}
            # Persist intent before the only write request. A restart must not resubmit.
            await self.save()
            try:
                receipt = await self.bridge("start_recipe_upload", {"recipes": self.job["programs"]})
                if not isinstance(receipt.get("job_id"), str) or not receipt["job_id"]:
                    raise HomeAssistantError("Uploadantwort enthält keine Auftrags-ID.")
                if receipt.get("result") not in ("queued", "sending", "confirmed", "state_changed", "unconfirmed"):
                    raise HomeAssistantError("Ungültiger Auftragsstatus.")
                self.job.update(receipt)
            except asyncio.CancelledError:
                self.job["result"] = "outcome_unknown"
                await asyncio.shield(self.save())
                raise
            except Exception as err:
                self.job["result"] = "outcome_unknown"
                await self.save()
                raise HomeAssistantError("Uploadausgang unklar. Nicht erneut senden; Gerät und Bridge prüfen.") from err
            await self.save()
            return self.state()
        if action == "status":
            await self.refresh_status()
            return self.state()
        if action == "acknowledge_unknown":
            if not self.job or self.job.get("result") not in ACTIVE or data.get("device_checked") is not True:
                raise HomeAssistantError("Nur nach manueller Prüfung des Geräts und eines beendeten Auftrags freigeben.")
            self.job["result"] = "manually_released"
            await self.save()
            return self.state()
        raise HomeAssistantError("Unbekannte HBAC-Aktion.")

    async def refresh_status(self):
        if not self.job or not self.job.get("job_id"):
            raise HomeAssistantError("Keine Auftrags-ID vorhanden. Gerät und Bridge manuell prüfen.")
        receipt = await self.bridge("recipe_upload_status", {"job_id": self.job["job_id"]})
        if receipt.get("job_id") != self.job["job_id"] or receipt.get("result") not in (
                "queued", "sending", "confirmed", "state_changed", "unconfirmed"):
            raise HomeAssistantError("Unpassende Bridge-Auftragsantwort.")
        self.job.update(receipt)
        await self.save()

    async def poll(self, _now):
        if self.lock.locked() or not self.job or not self.job.get("job_id"):
            return
        if time.time() - self.job.get("started_at", 0) > 180:
            return
        if self.job.get("result") not in ("queued", "sending") and not (
                self.job.get("result") == "confirmed" and self.job.get("content_verification", "not_available") == "not_available"):
            return
        try:
            await self.dispatch("status", {})
        except HomeAssistantError:
            self.error = "Auftragsstatus derzeit nicht abrufbar. Kein erneuter Upload; Status später abfragen."
            self.notify()
