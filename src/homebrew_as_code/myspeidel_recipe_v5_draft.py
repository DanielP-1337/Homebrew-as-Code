"""Offline recipe_v5 candidate and structural OpenAPI audit; NEVER a write payload.

No vendor examples, credentials or private recipes are emitted.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .recipe import load_recipe, validate_recipe
from .myspeidel_openapi_reference import _pointer, inspect_spec


def build_candidate(recipe: dict[str, Any]) -> dict[str, Any]:
    """Only map values whose *scalar* correspondence is known.

    Boil and mash shapes are not projected until nested semantics/UUIDs are
    checked against vendor evidence. This fragment MUST NOT be POSTed.
    """
    validate_recipe(recipe)
    return {
        "name": recipe["recipe"]["name"],
        "bitterness": recipe["targets"]["bitterness_ibu"],
    }


def _check(node: Any, schema: dict[str, Any], spec: dict[str, Any], path: str,
           issues: list[dict[str, str]], depth: int = 0, refs: tuple[str, ...] = ()) -> None:
    if depth > 40:
        issues.append({"path": path, "code": "SCHEMA_DEPTH_LIMIT"})
        return
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in refs:
            issues.append({"path": path, "code": "RECURSIVE_SCHEMA_UNSUPPORTED"})
            return
        _check(node, _pointer(spec, ref), spec, path, issues, depth + 1, (*refs, ref))
        return
    # OpenAPI 3.0 nullable is allowed; avoid assuming JSON Schema 2020 semantics.
    if node is None and schema.get("nullable") is True:
        return
    typ = schema.get("type")
    conforms = {"object": lambda x: isinstance(x, dict),
                "array": lambda x: isinstance(x, list),
                "string": lambda x: isinstance(x, str),
                "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
                "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
                "boolean": lambda x: isinstance(x, bool)}
    if typ in conforms and not conforms[typ](node):
        issues.append({"path": path, "code": "TYPE_MISMATCH"})
        return
    if "enum" in schema and node not in schema["enum"]:
        issues.append({"path": path, "code": "ENUM_MISMATCH"})
    if isinstance(node, dict):
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            if field not in node:
                issues.append({"path": f"{path}.{field}", "code": "REQUIRED_MISSING"})
        for key, value in node.items():
            sub = properties.get(key)
            if sub is None:
                extra = schema.get("additionalProperties", True)
                if extra is False:
                    issues.append({"path": f"{path}.{key}", "code": "ADDITIONAL_PROPERTY"})
                elif isinstance(extra, dict):
                    _check(value, extra, spec, f"{path}.{key}", issues, depth + 1, refs)
            else:
                _check(value, sub, spec, f"{path}.{key}", issues, depth + 1, refs)
    if isinstance(node, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(node):
            _check(item, schema["items"], spec, f"{path}[{i}]", issues, depth + 1, refs)
    # Unsupported composition keywords are explicitly diagnosed, never ignored.
    if any(k in schema for k in ("allOf", "anyOf", "oneOf", "not", "discriminator")):
        issues.append({"path": path, "code": "COMPOSITION_REQUIRES_EXTERNAL_VALIDATOR"})


def inspect_candidate(spec: dict[str, Any], recipe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = inspect_spec(spec, recipe)
    candidate = build_candidate(recipe)
    issues: list[dict[str, str]] = []
    _check(candidate, _pointer(spec, "#/components/schemas/recipe_v5"), spec, "$", issues)
    required_missing = [i["path"] for i in issues if i["code"] == "REQUIRED_MISSING"]
    semantic_blockers = [
        "Verify MySpeidel catalog references and ingredient UUIDs before mapping malts/hops/spices",
        "Validate nested mash, rest, boil, fermentation, maturation and phases against a real private GET recipe",
        "Resolve POST server-managed identity fields from documented semantics; do not invent UUIDs or timestamps",
        "Confirm units and acceptable numeric ranges for every mapped value (including bitterness)",
        "Compare complete candidate with official schema using an independent OpenAPI 3.0 validator before any dryRun",
    ]
    report = {
        "format": "homebrew-as-code/myspeidel-recipe-v5-draft-report-v1",
        "schema_reference": "#/components/schemas/recipe_v5",
        "offline": True,
        "structure_checked_subset": ["type", "required", "properties", "additionalProperties", "items", "enum", "$ref", "nullable"],
        "openapi_full_validation": False,
        "structurally_complete": not issues,
        "upload_ready": False,
        "api_payload": None,
        "candidate_fields": sorted(candidate),
        "missing_required_paths": sorted(required_missing),
        "schema_issues": issues,
        "semantic_blockers": semantic_blockers,
        "reference_inventory_required": inventory["api_required_fields"],
        "example_missing_required": inventory["example_missing_required"],
        "api_operations_verified": inventory["post_supports_recipe_v5"] and inventory["get_returns_recipe_v5"],
        "notes": "Candidate is a partial, non-uploadable structural fragment; third-party sample is not redistributed.",
    }
    return candidate, report


def inspect_files(spec_path: str | Path, recipe_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = Path(spec_path).read_bytes()
    spec = json.loads(raw)
    candidate, report = inspect_candidate(spec, load_recipe(recipe_path))
    report["spec_sha256"] = hashlib.sha256(raw).hexdigest()
    return candidate, report
