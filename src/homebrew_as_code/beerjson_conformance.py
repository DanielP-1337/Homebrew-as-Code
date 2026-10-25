"""Pinned, offline schema validation; no domain import or vendor compatibility claim."""
from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft7Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

SCHEMA_TARGET = "beerjson-v1-a3c0c0c"


def _deny_retrieval(uri: str) -> Resource:
    raise NoSuchResource(ref=uri)


class SchemaIntegrityError(RuntimeError):
    """The local validator bundle is damaged, not the inspected input."""


def load_validator() -> tuple[Draft7Validator, dict[str, Any]]:
    """Verify LF-normalized vendored bytes; resolve locally, never via HTTP."""
    directory = files("homebrew_as_code").joinpath("schemas/beerjson_v1")
    manifest = json.loads(directory.joinpath("manifest.json").read_text(encoding="utf-8"))
    registry = Registry(retrieve=_deny_retrieval)
    schemas = {}
    for name, digest in manifest["files"].items():
        # Git can convert text to CRLF in Windows worktrees. Only normalize
        # that transport difference; do not strip whitespace, BOMs or reserialize.
        content = directory.joinpath(name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(content).hexdigest() != digest:
            raise SchemaIntegrityError(f"Vendored schema integrity failure: {name}")
        if name.endswith(".json"):
            schema = json.loads(content)
            Draft7Validator.check_schema(schema)
            schemas[name] = schema
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return Draft7Validator(schemas[manifest["root"]], registry=registry,
                           format_checker=FormatChecker()), manifest


def validate_beerjson(document: Any, *, schema_target: str) -> dict[str, Any]:
    """Schema validity is independent from version policy and application support.

    The upstream VersionType accepts any number. Do not rewrite version 2.06
    to 1, and do not describe a passing schema check as verified interoperability.
    Error messages omit input values to reduce accidental private-data disclosure.
    """
    if schema_target != SCHEMA_TARGET:
        raise ValueError(f"Unsupported schema target: {schema_target}")
    validator, manifest = load_validator()
    root = document.get("beerjson") if isinstance(document, dict) else None
    version = root.get("version") if isinstance(root, dict) else None
    errors = sorted(validator.iter_errors(document),
                    key=lambda error: (str(list(error.absolute_path)), str(list(error.absolute_schema_path))))
    return {
        "schema_target": schema_target,
        "schema_commit": manifest["commit"],
        "declared_version": version,
        "schema_valid": not errors,
        "version_policy_match": type(version) in (int, float) and version == 1,
        "version_policy": "Only numeric 1/1.0 is selected by this adapter; other versions are unverified.",
        "application_compatibility": "not_tested",
        "import_ready": False,
        "errors": [{"path": list(e.absolute_path), "schema_path": list(e.absolute_schema_path),
                    "keyword": e.validator} for e in errors],
    }
