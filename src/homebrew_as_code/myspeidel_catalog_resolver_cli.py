"""Run offline, privacy-conscious MySpeidel catalog matching."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import yaml
from .recipe import load_recipe
from .myspeidel_catalog_resolver import resolve_snapshot


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline MySpeidel catalog reference resolver (never sends requests)")
    p.add_argument("recipe")
    p.add_argument("--spec", required=True, help="Locally downloaded official OpenAPI JSON")
    p.add_argument("--snapshot", required=True, help="Private user-confirmed catalog snapshot YAML")
    p.add_argument("--output", required=True, help="Private report path under .local")
    args = p.parse_args(argv)
    try:
        dest = Path(args.output)
        if dest.exists():
            raise ValueError("Refusing to overwrite report")
        if ".local" not in dest.parts:
            raise ValueError("Output must be within a .local directory")
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        snapshot = yaml.safe_load(Path(args.snapshot).read_text(encoding="utf-8"))
        result = resolve_snapshot(load_recipe(args.recipe), spec, snapshot)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(f"OFFLINE REPORT: {dest}")
        print(f"Resolved: {result['resolved_count']} / {result['recipe_count']}")
        print("No API calls. No recipe upload. Catalog matches require independent verification.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError):
        print("ERROR: catalog inspection failed (private details suppressed)", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
