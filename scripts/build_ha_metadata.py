"""Generate native HA translations from the same JSON files as the dashboard."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/hbac"
LOCALES = COMPONENT / "frontend/locales"
fallback = json.loads((LOCALES / "en-US.json").read_text(encoding="utf-8"))
services = yaml.safe_load((COMPONENT / "services.yaml").read_text(encoding="utf-8"))
action_keys = {"import_file": "ui.file_upload", "open_file": "ui.open_file", "state": "ui.state", "catalog": "ui.load_catalog", "preview": "ui.preview", "add": "ui.add",
               "remove": "ui.remove", "move": "ui.move", "clear": "ui.clear", "readiness": "ui.readiness",
               "upload": "ui.upload", "status": "ui.refresh_status", "acknowledge_unknown": "ui.release"}
field_keys = {"review_steps": "ui.step_review", "source_token": "ui.source_token", "step_roles": "ui.step_roles", "content": "ui.file_upload", "filename": "ui.file", "entry_id": None, "kind": "ui.source", "refresh": "ui.refresh", "source_id": "ui.source_id",
              "mash_in": "ui.mash_in", "boil_temperature": "ui.boil_temperature", "preview_id": "ui.preview_id",
              "revision": "ui.revision", "index": "ui.index", "target": "ui.target", "replace_all": "ui.consent",
              "device_checked": "ui.release_confirm"}


def generate(catalog):
    def t(key):
        return catalog.get(key) or fallback[key]

    data = {"user_id": t("config.user_id"), "api_key": t("config.api_key"), "brewersfriend_api_key": t("config.brewersfriend_api_key"), "import_directory": t("config.import_directory")}
    result = {"title": "HBAC – Recipes to Braumeister", "config": {
        "step": {"user": {"title": t("config.setup"), "description": t("config.description"),
                           "data": {**data, "bridge_entry_id": "Braumeister"}},
                 "reconfigure": {"title": t("config.reconfigure"), "description": t("config.description"), "data": data}},
        "error": {key: t("config." + key) for key in ("invalid_auth", "cannot_connect", "incomplete_brewfather", "invalid_directory")},
        "abort": {key: t("config." + key) for key in ("no_bridge", "already_configured")}},
        "services": {}, "exceptions": {},
        "entity": {"sensor": {"upload": {"name": t("ui.status_title"), "state": {"idle": t("ui.idle")}}}}}
    result["config"]["abort"]["reconfigure_successful"] = t("config.updated")
    for name, service in services.items():
        title = t(action_keys[name])
        description = t("ui.replace_warning") if name == "upload" else t("ui.recovery_warning") if name == "acknowledge_unknown" else title
        result["services"][name] = {"name": title, "description": description,
            "fields": {field: {"name": t(field_keys[field]) if field_keys[field] else "HBAC"} for field in service["fields"]}}
    for key in fallback:
        if key.startswith("runtime."):
            result["exceptions"][key.replace(".", "_")] = {"message": t(key)}
        if key.startswith("status."):
            result["entity"]["sensor"]["upload"]["state"][key.split(".", 1)[1]] = t(key)
    return result


for path in sorted(LOCALES.glob("*.json")):
    locale = "en" if path.stem == "en-US" else path.stem
    catalog = json.loads(path.read_text(encoding="utf-8"))
    result = generate(catalog)
    (COMPONENT / "translations" / f"{locale}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
english = generate(fallback)
(COMPONENT / "strings.json").write_text(json.dumps(english, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for name, service in services.items():
    service["name"] = english["services"][name]["name"]
    service["description"] = english["services"][name]["description"]
    for field, schema in service["fields"].items():
        schema["name"] = english["services"][name]["fields"][field]["name"]
(COMPONENT / "services.yaml").write_text(yaml.safe_dump(services, allow_unicode=True, sort_keys=False), encoding="utf-8")
