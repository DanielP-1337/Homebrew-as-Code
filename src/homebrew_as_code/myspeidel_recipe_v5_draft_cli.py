"""Offline-only recipe_v5 draft inventory. No requests or API writer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .myspeidel_recipe_v5_draft import inspect_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline non-uploadable MySpeidel recipe_v5 candidate and schema issues")
    parser.add_argument("recipe")
    parser.add_argument("--spec", required=True, help="Locally downloaded MySpeidel OpenAPI JSON")
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args(argv)
    prefix = Path(args.output_prefix)
    dests = [Path(str(prefix) + suffix) for suffix in (".candidate.json", ".report.json")]
    try:
        if any(p.exists() for p in dests):
            raise ValueError("Refusing to overwrite existing outputs")
        candidate, report = inspect_files(args.spec, args.recipe)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        for dest, value in zip(dests, (candidate, report)):
            dest.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"OFFLINE CANDIDATE (NEVER UPLOAD): {dests[0]}")
        print(f"SCHEMA/BLOCKER REPORT: {dests[1]}")
        print(f"Missing required top-level fields: {len(report['missing_required_paths'])}")
        print("UPLOAD DISABLED. No POST, PUT, dryRun or network calls.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: offline mapping failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
