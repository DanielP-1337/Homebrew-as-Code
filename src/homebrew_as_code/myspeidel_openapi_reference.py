"""Inspect an explicitly downloaded, local MySpeidel OpenAPI specification.

No HTTP requests, credentials, recipe uploads or vendor sample redistribution.
This is a schema inventory, NOT a full JSON Schema validator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .recipe import load_recipe

OPENAPI_URL = "https://api.cloud.myspeidel.com/v1.0/api-spec/json"
RECIPE_REF = "#/components/schemas/recipe_v5"
EXAMPLE_REF = "#/components/examples/recipe"

# Names of source-domain concepts, not one-to-one API conversions.
# Presence of a name here does NOT assert equivalent units or semantics.
DOMAIN_CANDIDATES = {
    "name": "recipe.name",
    "style": "recipe.style",
    "bitterness": "targets.bitterness_ibu",
    "machine_type": "equipment.model",
    "mashing": "mash.steps",
    "boil": "boil",
    "fermentation": "yeast.fermentation_temperature_c",
}


def _pointer(document: dict[str, Any], reference: str) -> Any:
    if not isinstance(reference, str) or not reference.startswith("#/"):
        raise ValueError("Only local OpenAPI JSON pointers are supported")
    current: Any = document
    for part in reference[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise ValueError("Unresolvable OpenAPI reference")
        current = current[part]
    return current


def _refs_in(node: Any) -> set[str]:
    if isinstance(node, dict):
        values = {node["$ref"]} if isinstance(node.get("$ref"), str) else set()
        for child in node.values():
            values.update(_refs_in(child))
        return values
    if isinstance(node, list):
        result: set[str] = set()
        for child in node:
            result.update(_refs_in(child))
        return result
    return set()


def _get(recipe: dict[str, Any], path: str) -> bool:
    current: Any = recipe
    for component in path.split("."):
        if not isinstance(current, dict) or component not in current:
            return False
        current = current[component]
    return current is not None


def inspect_spec(spec: dict[str, Any], recipe: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict) or not str(spec.get("openapi", "")).startswith("3."):
        raise ValueError("Expected an OpenAPI 3.x object")
    schema = _pointer(spec, RECIPE_REF)
    if not isinstance(schema, dict) or not isinstance(schema.get("properties"), dict) or not isinstance(schema.get("required"), list):
        raise ValueError("recipe_v5 schema must declare properties and required")
    example_wrapper = _pointer(spec, EXAMPLE_REF)
    if not isinstance(example_wrapper, dict) or not isinstance(example_wrapper.get("value"), dict):
        raise ValueError("Official recipe example must have an object value")
    example = example_wrapper["value"]
    post = spec.get("paths", {}).get("/v1.0/recipe", {}).get("post", {})
    get = spec.get("paths", {}).get("/v1.0/recipe/{uuid}", {}).get("get", {})
    if not isinstance(post, dict) or not isinstance(get, dict):
        raise ValueError("Expected recipe POST and GET operations")
    post_body = post.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    get_body = get.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})
    post_refs = sorted(_refs_in(post_body))
    if RECIPE_REF not in post_refs or get_body.get("$ref") != RECIPE_REF:
        raise ValueError("Recipe operations do not advertise recipe_v5 as expected")
    required = schema["required"]
    if any(not isinstance(x, str) for x in required):
        raise ValueError("Invalid required field list")
    rows = []
    for name in sorted(schema["properties"]):
        source_path = DOMAIN_CANDIDATES.get(name)
        rows.append({
            "api_field": name, "required": name in required,
            "in_official_example": name in example,
            "domain_candidate": source_path,
            "source_present": _get(recipe, source_path) if source_path else False,
            "mapping_verified": False,
            "status": "CANDIDATE_REQUIRES_SEMANTIC_VALIDATION" if source_path and _get(recipe, source_path) else "UNMAPPED_OR_UNKNOWN",
        })
    return {
        "format": "homebrew-as-code/myspeidel-openapi-reference-v1",
        "offline": True, "schema_reference": RECIPE_REF,
        "example_reference": EXAMPLE_REF,
        "openapi_version": spec["openapi"],
        "post_supports_recipe_v5": True, "get_returns_recipe_v5": True,
        "post_parameter_names": sorted(x.get("name") for x in post.get("parameters", []) if isinstance(x, dict) and isinstance(x.get("name"), str)),
        "api_required_fields": sorted(required),
        "example_missing_required": sorted(set(required) - set(example)),
        "fields": rows,
        "upload_ready": False,
        "api_payload": None,
        "notes": [
            "Schema inventory only; no recursive type, unit or semantic validation.",
            "Official example inspected in memory, not included in output.",
            "No invented UUIDs, references, defaults, credentials or API writes.",
        ],
    }


def inspect_files(spec_path: str | Path, recipe_path: str | Path) -> dict[str, Any]:
    raw = Path(spec_path).read_bytes()
    spec = json.loads(raw)
    report = inspect_spec(spec, load_recipe(recipe_path))
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    report["source_url"] = OPENAPI_URL
    return report
