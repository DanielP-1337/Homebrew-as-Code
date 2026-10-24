"""Offline inspection and conservative resolution of MySpeidel catalog references.

Never connects to the internet, synthesizes UUIDs, or creates upload payloads.
Snapshots require independent user verification: a documented GET path alone is
not proof that a particular catalog object is valid for recipe_v5.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from .recipe import validate_recipe

KINDS = ("malt", "hop", "ingredient", "water")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}$")


def api_get_inventory(spec: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(spec, dict) or not str(spec.get("openapi", "")).startswith("3.0."):
        raise ValueError("Expected OpenAPI 3.0 specification")
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI paths missing")
    rows = []
    for path, methods in sorted(paths.items()):
        if not isinstance(path, str) or not isinstance(methods, dict) or "get" not in methods:
            continue
        op = methods["get"]
        if not isinstance(op, dict):
            continue
        # This is discovery, not a claim of an authorized callable endpoint.
        if any(term in path.casefold() for term in ("malt", "hop", "ingredient", "water", "catalog")):
            rows.append({"method": "GET", "path": path, "operation_id": op.get("operationId"),
                         "documented": True, "authorized_for_client": False})
    return rows


def _uuid(value: Any) -> bool:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        return False
    try:
        return str(UUID(value)) == value.casefold()
    except ValueError:
        return False


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _recipe_items(recipe: dict[str, Any]) -> list[dict[str, str]]:
    validate_recipe(recipe)
    items = [{"name": malt["name"], "kind": "malt"} for malt in recipe["fermentables"]]
    for a in recipe["boil"].get("additions", []):
        items.append({"name": a["ingredient"],
                      "kind": "hop" if "alpha_acid_percent" in a else "ingredient"})
    return items


def resolve_snapshot(recipe: dict[str, Any], spec: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    """Resolve names only against explicitly confirmed, documented local entries.

    Snapshot format:
      schema_version: 1
      entries:
        - {kind: malt, name: ..., uuid: ..., source_get_path: ..., confirmed: true}
    A private GET observation can justify a catalog source only after explicit
    inspection of the documented GET operation and manual confirmation.
    """
    inventory = api_get_inventory(spec)
    documented_gets = {row["path"] for row in inventory}
    if not isinstance(snapshot, dict) or type(snapshot.get("schema_version")) is not int or snapshot["schema_version"] != 1:
        raise ValueError("Snapshot schema_version must be 1")
    entries = snapshot.get("entries")
    if not isinstance(entries, list) or len(entries) > 10000:
        raise ValueError("Snapshot entries must be a bounded list")
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"entry {i} must be mapping")
        kind, name, uid, path, confirmed = (entry.get(k) for k in
                                            ("kind", "name", "uuid", "source_get_path", "confirmed"))
        if kind not in KINDS or not isinstance(name, str) or not name.strip() or not _uuid(uid):
            raise ValueError(f"entry {i}: invalid kind/name/UUID")
        private_get = (path == "/v1.0/recipe/{uuid}" and
                       entry.get("provenance") == "manually_confirmed_private_recipe_get" and
                       entry.get("web_verified") is True and
                       isinstance(entry.get("observed_container"), str) and
                       entry["observed_container"].startswith(("$.mashing.adds.malts[", "$.boil.steps[")) and
                       isinstance(spec.get("paths", {}).get("/v1.0/recipe/{uuid}", {}).get("get"), dict))
        catalog_get = (isinstance(path, str) and path.startswith("/v1.0/") and
                       "{" not in path and path in documented_gets)
        if not (private_get or catalog_get):
            raise ValueError(f"entry {i}: source must be documented catalog GET or manually confirmed private recipe GET")
        if type(confirmed) is not bool:
            raise ValueError(f"entry {i}: confirmed must be boolean")
        index.setdefault((kind, _normalized(name)), []).append(entry)
    rows = []
    for item in _recipe_items(recipe):
        matches = index.get((item["kind"], _normalized(item["name"])), [])
        # Never silently collapse duplicate rows, even if UUIDs happen to match.
        if len(matches) > 1:
            status, uid, reason = "AMBIGUOUS", None, "Multiple exact catalog entries"
        elif not matches:
            status, uid, reason = "UNRESOLVED", None, "No exact category-and-name match"
        elif matches[0]["confirmed"] is not True:
            status, uid, reason = "UNCONFIRMED", None, "Catalog entry not explicitly confirmed"
        else:
            status, uid, reason = "MATCHED", matches[0]["uuid"], "Confirmed exact match in local snapshot"
        rows.append({"ingredient": item["name"], "requested_kind": item["kind"],
                     "status": status, "catalog_uuid": uid, "reason": reason})
    return {"format": "homebrew-as-code/myspeidel-catalog-resolution-v1", "offline": True,
            "upload_ready": False, "api_payload": None, "recipe_count": len(rows),
            "resolved_count": sum(x["status"] == "MATCHED" for x in rows),
            "documented_catalog_get_endpoints": inventory,
            "rows": rows,
            "blockers": ["Unconfirmed catalog entries or unresolved ingredients must not be used for uploads",
                         "Ingredient category is a proposal; verify unusual spices/honey in MySpeidel UI",
                         "No authenticated catalog GET is implemented or authorized by this tool",
                         "Water, yeast, and recipe metadata references still require separate verification",
                         "No MySpeidel recipe POST/PUT or dryRun is performed"]}
