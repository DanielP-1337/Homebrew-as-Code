"""Read-only format probes, separate from canonical recipe/equipment/brew-plan models."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .beerjson_conformance import SCHEMA_TARGET, SchemaIntegrityError, validate_beerjson


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def inspect_document(content: bytes, *, schema_target: str) -> dict[str, Any]:
    """Identify structures, never trust extensions or infer lossless equivalence."""
    if schema_target != SCHEMA_TARGET:
        raise ValueError(f"Unsupported schema target: {schema_target}")
    text = content.decode("utf-8-sig")
    result: dict[str, Any] = {
        "sha256": hashlib.sha256(content).hexdigest(),
        "format": "unknown", "schema_valid": None,
        "application_compatibility": "not_tested", "import_ready": False,
    }
    if text.lstrip().startswith("<"):
        # Exchange documents do not need DTDs or entity declarations.
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise ValueError("XML DTD/entity declarations are not supported")
        root = ET.fromstring(text)
        if root.tag == "RECIPES":
            recipes = root.findall("RECIPE")
            versions = [r.findtext("VERSION") for r in recipes]
            result.update(format="beerxml", declared_versions=versions,
                          recipe_count=len(recipes),
                          version_policy_match=bool(recipes) and all(v == "1" for v in versions),
                          validation="structure_probe_only; no BeerXML schema validation")
        elif root.tag.split("}")[-1] == "BeerXML":
            result.update(format="beerxml_2_candidate", validation="unsupported_draft")
        return result
    document = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_nonfinite)
    if isinstance(document, dict) and "beerjson" in document:
        result.update(format="beerjson")
        result.update(validate_beerjson(document, schema_target=schema_target))
        root = document["beerjson"]
        recipes = root.get("recipes") if isinstance(root, dict) else None
        result["recipe_count"] = len(recipes) if isinstance(recipes, list) else None
    elif (isinstance(document, dict) and "_versionId" in document
          and isinstance(document.get("fermentables"), list)
          and isinstance(document.get("yeasts"), list)):
        result.update(format="brewfather_json_candidate",
                      validation="vendor_structure_probe_only; no public schema selected")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline multi-format inspection; no imports or uploads")
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--schema-target", required=True, choices=[SCHEMA_TARGET])
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.report.resolve() in {p.resolve() for p in args.inputs}:
            raise ValueError("Report must not replace an input")
        results = []
        for index, path in enumerate(args.inputs):
            try:
                results.append({"input_index": index, **inspect_document(
                    path.read_bytes(), schema_target=args.schema_target)})
            except (ValueError, UnicodeError, OSError, ET.ParseError) as exc:
                # Do not put private paths, contents, or parser snippets in reports.
                results.append({"input_index": index, "format": "unreadable",
                                "error_type": type(exc).__name__, "import_ready": False})
        report = {"format": "homebrew-as-code/interoperability-report-v1",
                  "semantic_equivalence": "not_evaluated", "inputs": results}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print("Inspection report written; application compatibility remains unverified.")
        # Success requires every input to pass the selected schema AND version policy.
        return 0 if all(r.get("schema_valid") is True and r.get("version_policy_match") is True
                        for r in results) else 2
    except SchemaIntegrityError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print(f"ERROR: {type(exc).__name__}; inspection could not complete", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
