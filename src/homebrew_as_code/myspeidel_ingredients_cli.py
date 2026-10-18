"""Offline ingredient plan CLI. No authentication, HTTP or file writes."""
from __future__ import annotations

import argparse
import json
import sys

from .myspeidel_ingredients import build_ingredient_plan_file
from .myspeidel_mapper import MappingError
from .recipe import RecipeError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline MySpeidel ingredient plan (NOT uploadable)')
    parser.add_argument('recipe', nargs='?', default='recipes/lebkuchen-zauber/recipe.yaml')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build_ingredient_plan_file(args.recipe), ensure_ascii=False, indent=2))
        return 0
    except (RecipeError, MappingError, OSError, ValueError):
        print('ERROR: Could not build offline ingredient plan', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
