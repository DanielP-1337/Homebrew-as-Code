"""Offline BeerJSON draft export. Never uploads or reads credentials."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .beerjson_export import build_beerjson_draft_file
from .recipe import RecipeError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export an INCOMPLETE BeerJSON draft and a blockers report")
    parser.add_argument("recipe", nargs="?", default="recipes/lebkuchen-zauber/recipe.yaml")
    parser.add_argument("--output", required=True, help="Destination .beerjson file (not import-ready)")
    args = parser.parse_args(argv)
    try:
        draft, report = build_beerjson_draft_file(args.recipe)
        destination = Path(args.output)
        if destination.suffix.lower() != ".beerjson":
            raise ValueError("Output must have .beerjson suffix")
        if destination.exists() or destination.with_suffix('.report.json').exists():
            raise ValueError("Output/report already exists; refusing to overwrite")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        destination.with_suffix('.report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"DRAFT written: {destination} (NOT schema-valid or MySpeidel import-ready)")
        print(f"BLOCKERS: {destination.with_suffix('.report.json')}")
        return 0
    except (RecipeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
