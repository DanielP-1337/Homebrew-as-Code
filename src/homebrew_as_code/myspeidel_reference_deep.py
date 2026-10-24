"""Offline, source-attributed inspection of MySpeidel recipe_v5 OpenAPI.

A diagnostic ONLY: does not derive an upload body, rewrite schema fields, or use network.
The vendor reference example is examined in memory and never copied to reports.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .myspeidel_openapi_reference import RECIPE_REF, EXAMPLE_REF, _pointer, _refs_in
from .recipe import load_recipe

# Routing categories describe the *next investigation*, not validated field mappings.
DOMAIN = {"name", "description", "style", "bitterness", "color", "water_plato",
          "water_specific_gravity", "water_recast", "mashing", "rest", "boil",
          "fermentation", "maturation"}
ADAPTER = {"machine_type", "brewer", "country", "comments", "recipe_type",
           "phases", "schema_version", "brewing_set_active", "public"}
API_REFERENCE = {"references", "owner"}
UNCERTAIN = {"uuid", "parent_uuid", "created_on", "update_on", "content_version"}


def _category(name: str) -> str:
    if name in DOMAIN:
        return "RECIPE_DOMAIN_CANDIDATE"
    if name in ADAPTER:
        return "ADAPTER_CONFIGURATION_CANDIDATE"
    if name in API_REFERENCE:
        return "API_REFERENCE_REQUIRED"
    return "UNKNOWN_POST_SEMANTICS"


def _resolve(spec: dict, node: Any, seen: frozenset[str] = frozenset()) -> dict:
    if not isinstance(node, dict):
        return {}
    if "$ref" not in node:
        return node
    ref = node["$ref"]
    if ref in seen:
        raise ValueError("Circular OpenAPI schema reference")
    resolved = _pointer(spec, ref)
    if not isinstance(resolved, dict):
        raise ValueError("OpenAPI schema reference is not an object")
    return _resolve(spec, resolved, seen | {ref})


def _type_names(node: dict) -> list[str]:
    typ = node.get("type")
    if isinstance(typ, str):
        return [typ]
    if isinstance(typ, list):
        return [x for x in typ if isinstance(x, str)]
    return []


def _safe_shape(node: dict) -> dict:
    # Never copy descriptions, examples, defaults, enums or vendor sample values.
    return {
        "types": _type_names(node),
        "nullable": node.get("nullable") is True,
        "read_only": node.get("readOnly") is True,
        "write_only": node.get("writeOnly") is True,
        "has_default": "default" in node,
        "enum_count": len(node["enum"]) if isinstance(node.get("enum"), list) else None,
        "format": node.get("format") if isinstance(node.get("format"), str) else None,
        "minimum_defined": "minimum" in node,
        "maximum_defined": "maximum" in node,
    }


def _inspect_tree(spec: dict, schema: dict, example: Any, path: str,
                  depth: int, limit: int, seen: set[str]) -> list[dict]:
    if depth > limit:
        return [{"path": path, "truncated": "MAX_DEPTH"}]
    node = _resolve(spec, schema)
    row = {"path": path, **_safe_shape(node),
           "example_present": example is not _MISSING,
           "example_is_null": example is None if example is not _MISSING else None}
    if isinstance(example, dict):
        row["example_object_keys"] = len(example)
    if isinstance(example, list):
        row["example_array_length"] = len(example)
    rows = [row]
    # Follow only properties and arrays: no guessed semantics for oneOf/allOf.
    props = node.get("properties")
    if isinstance(props, dict):
        required = node.get("required") if isinstance(node.get("required"), list) else []
        for key in sorted(props):
            if not isinstance(key, str):
                continue
            childpath = f"{path}.{key}"
            child = props[key]
            if not isinstance(child, dict):
                continue
            nested_example = example.get(key, _MISSING) if isinstance(example, dict) else _MISSING
            children = _inspect_tree(spec, child, nested_example, childpath, depth + 1, limit, seen)
            children[0]["required_in_parent"] = key in required
            rows.extend(children)
    items = node.get("items")
    if isinstance(items, dict):
        first = example[0] if isinstance(example, list) and example else _MISSING
        rows.extend(_inspect_tree(spec, items, first, path + "[]", depth + 1, limit, seen))
    if any(x in node for x in ("allOf", "anyOf", "oneOf")):
        row["composition_requires_full_validator"] = True
    return rows


_MISSING = object()


def _operation_schema(spec: dict, kind: str) -> dict:
    paths = spec.get("paths", {})
    if kind == "post":
        op = paths.get("/v1.0/recipe", {}).get("post", {})
        return op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    op = paths.get("/v1.0/recipe/{uuid}", {}).get("get", {})
    responses = op.get("responses", {})
    return responses.get("200", {}).get("content", {}).get("application/json", {}).get("schema", {})


def inspect_deep(spec: dict[str, Any], recipe: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict) or not str(spec.get("openapi", "")).startswith("3."):
        raise ValueError("Expected OpenAPI 3.x document")
    schema = _resolve(spec, {"$ref": RECIPE_REF})
    if not isinstance(schema.get("properties"), dict):
        raise ValueError("recipe_v5 properties missing")
    example_wrapper = _pointer(spec, EXAMPLE_REF)
    if not isinstance(example_wrapper, dict) or not isinstance(example_wrapper.get("value"), dict):
        raise ValueError("Official recipe example missing")
    example = example_wrapper["value"]
    post_schema, get_schema = _operation_schema(spec, "post"), _operation_schema(spec, "get")
    post_refs, get_refs = sorted(_refs_in(post_schema)), sorted(_refs_in(get_schema))
    if RECIPE_REF not in post_refs or RECIPE_REF not in get_refs:
        raise ValueError("POST or GET does not reference recipe_v5")
    fields = []
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise ValueError("Invalid recipe_v5 required list")
    for name, definition in sorted(schema["properties"].items()):
        if not isinstance(definition, dict):
            continue
        resolved = _resolve(spec, definition)
        fields.append({"field": name, "required": name in required,
                       "in_example": name in example, "classification": _category(name),
                       **_safe_shape(resolved)})
    missing = sorted(set(required) - set(example))
    # Distinguish a shared schema from server-managed semantics. Do not infer POST behavior.
    post_params = spec.get("paths", {}).get("/v1.0/recipe", {}).get("post", {}).get("parameters", [])
    parameters = sorted(x["name"] for x in post_params if isinstance(x, dict) and isinstance(x.get("name"), str))
    return {
        "format": "homebrew-as-code/myspeidel-reference-deep-v1",
        "offline": True, "upload_ready": False, "api_payload": None,
        "schema_reference": RECIPE_REF, "example_reference": EXAMPLE_REF,
        "post_schema_references": post_refs, "get_schema_references": get_refs,
        "post_get_share_recipe_v5": RECIPE_REF in post_refs and RECIPE_REF in get_refs,
        "post_parameters": parameters,
        "required_top_level": sorted(required),
        "example_missing_required": missing,
        "example_present_top_level_count": len(example),
        "fields": fields,
        "nested_schema": {key: _inspect_tree(spec, schema["properties"][key], example.get(key, _MISSING), "$." + key, 0, 9, set())
                          for key in ("mashing", "rest", "boil", "fermentation", "maturation", "phases", "references")
                          if key in schema["properties"]},
        "blockers": [
            "Shared POST/GET recipe_v5 schema does not establish which identity/timestamp fields the POST server fills.",
            "Nested type/example inspection is not complete OpenAPI 3.0 validation; composition and semantic constraints require dedicated checks.",
            "Resolve ingredient and water catalog UUIDs using authorized evidence before mapping.",
            "Verify units, phase order and recipe semantics against controlled private GET roundtrip.",
            "No vendor sample values, UUIDs, dates or production metadata are generated.",
        ],
    }


def inspect_deep_files(spec_path: str | Path, recipe_path: str | Path) -> dict:
    raw = Path(spec_path).read_bytes()
    report = inspect_deep(json.loads(raw), load_recipe(recipe_path))
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    return report
