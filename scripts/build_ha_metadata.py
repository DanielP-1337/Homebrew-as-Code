"""Generate HA descriptions and translations from the action contract."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "hbac"
fields = {
    "entry_id": {"name": "HBAC-Integration", "required": False, "selector": {"config_entry": {"integration": "hbac"}}},
    "kind": {"name": "Quelle", "required": True, "selector": {"select": {"options": ["recipes", "batches"]}}},
    "refresh": {"name": "Cache aktualisieren", "default": False, "selector": {"boolean": {}}},
    "source_id": {"name": "Brewfather-ID", "required": True, "selector": {"text": {}}},
    "mash_in": {"name": "Einmaischtemperatur (leer: erste Rast)", "selector": {"number": {"min": 20, "max": 80, "step": 1, "unit_of_measurement": "°C", "mode": "box"}}},
    "boil_temperature": {"name": "Kochtemperatur", "default": 103, "selector": {"number": {"min": 95, "max": 105, "step": 1, "unit_of_measurement": "°C", "mode": "box"}}},
    "preview_id": {"name": "Vorschau-ID", "required": True, "selector": {"text": {}}},
    "revision": {"name": "Aktuelle Listenrevision", "required": True, "selector": {"text": {}}},
    "index": {"name": "Listenindex (0–8)", "required": True, "selector": {"number": {"min": 0, "max": 8, "step": 1, "mode": "box"}}},
    "target": {"name": "Zielindex (0–8)", "required": True, "selector": {"number": {"min": 0, "max": 8, "step": 1, "mode": "box"}}},
    "replace_all": {"name": "Alle Geräterezeptplätze ersetzen", "required": True, "selector": {"boolean": {}}},
    "device_checked": {"name": "Gerät manuell geprüft, kein Auftrag läuft mehr", "required": True, "selector": {"boolean": {}}},
}
actions = {
    "state": ("Liste und Status lesen", "Liest die lokale Liste und den zuletzt bekannten Auftragsstatus.", []),
    "catalog": ("Brewfather-Liste abrufen", "Listet Rezepte oder Batches mit Paginierung; fünf Minuten Cache.", ["kind", "refresh"]),
    "preview": ("Rezept konvertieren", "Lädt den vollständigen Datensatz und erstellt eine Vorschau. Batch verwendet sein eigenes Rezept.", ["kind", "source_id", "mash_in", "boil_temperature"]),
    "add": ("Geprüfte Vorschau hinzufügen", "Fügt die unveränderte Vorschau der Upload-Liste hinzu.", ["preview_id", "revision"]),
    "remove": ("Listenplatz entfernen", "Entfernt einen Platz aus der lokalen Upload-Liste.", ["index", "revision"]),
    "move": ("Listenplatz verschieben", "Ändert die Reihenfolge der Geräterezeptplätze.", ["index", "target", "revision"]),
    "clear": ("Lokale Liste leeren", "Leert nur die lokale Liste, sendet nichts zum Gerät.", ["revision"]),
    "readiness": ("Gerätebereitschaft prüfen", "Fragt die aktuelle Bereitschaft über PR #30 ab.", []),
    "upload": ("Alle Geräteplätze ersetzen", "Ersetzt alle Geräterezeptplätze. Nur die geprüfte Listenrevision wird gesendet; kein automatischer Wiederholungsversuch.", ["revision", "replace_all"]),
    "status": ("Auftragsstatus abfragen", "Fragt genau die gespeicherte Auftrags-ID ab; sendet keine Rezepte.", []),
    "acknowledge_unknown": ("Uploads nach Geräteprüfung freigeben", "Nur nach manueller Prüfung, dass kein Upload mehr läuft. Sendet keine Rezepte.", ["device_checked"]),
}
services = {name: {"name": title, "description": desc, "fields": {key: fields[key] for key in ["entry_id", *keys]}}
            for name, (title, desc, keys) in actions.items()}
(COMPONENT / "services.yaml").write_text(yaml.safe_dump(services, allow_unicode=True, sort_keys=False), encoding="utf-8")
strings = {
    "title": "HBAC – Brewfather to Braumeister",
    "config": {"step": {
        "user": {"title": "Brewfather und Braumeister verbinden",
                 "description": "Brewfather API-Key mit recipes.read und batches.read verwenden. Zugangsdaten bleiben in Home Assistant.",
                 "data": {"user_id": "Brewfather User-ID", "api_key": "Brewfather API-Key", "bridge_entry_id": "Braumeister"}},
        "reconfigure": {"title": "Brewfather-Zugang erneuern", "data": {"user_id": "Brewfather User-ID", "api_key": "Neuer API-Key"}}},
        "error": {"invalid_auth": "Zugangsdaten ungültig oder Leserechte für Rezepte/Batches fehlen.", "cannot_connect": "Brewfather nicht erreichbar oder Anfragelimit erreicht."},
        "abort": {"no_bridge": "Zuerst die Speidel-Braumeister-Integration einrichten.", "already_configured": "HBAC ist für diesen Braumeister bereits eingerichtet.", "reconfigure_successful": "Zugangsdaten aktualisiert."}},
    "services": {name: {"name": definition["name"], "description": definition["description"],
                        "fields": {key: {"name": f["name"]} for key, f in definition["fields"].items()}}
                 for name, definition in services.items()},
}
(COMPONENT / "translations").mkdir(exist_ok=True)
for path in (COMPONENT / "strings.json", COMPONENT / "translations" / "de.json"):
    path.write_text(json.dumps(strings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
