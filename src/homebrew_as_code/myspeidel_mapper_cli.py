"""Print offline MySpeidel program subset; deliberately no upload capability."""
from __future__ import annotations

import argparse
import json
import sys

from .myspeidel_mapper import MappingError, map_program_file
from .recipe import RecipeError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build offline MySpeidel program fragment (NOT uploadable)")
    parser.add_argument("recipe", nargs="?", default="recipes/lebkuchen-zauber/recipe.yaml")
    args = parser.parse_args(argv)
    try:
        result = map_program_file(args.recipe)
    except (MappingError, RecipeError, OSError, ValueError):
        print("ERROR: Could not map recipe to confirmed program fields", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
