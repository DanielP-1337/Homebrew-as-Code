"""Interactive private-recipe selector and read-only structure inspector."""
from __future__ import annotations

import argparse
import getpass
import json
import sys

from .myspeidel import MySpeidelClient, MySpeidelError
from .myspeidel_auth import login
from .myspeidel_inspect import inspect_recipe, local_recipe_inventory, private_recipes
from .recipe import RecipeError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect one MySpeidel recipe (no content output)")
    parser.add_argument("--machine-size", type=int, default=20)
    parser.add_argument("--local-recipe", default="recipes/lebkuchen-zauber/recipe.yaml")
    args = parser.parse_args(argv)
    try:
        if args.machine_size <= 0:
            raise MySpeidelError("Invalid machine size")
        username = input("MySpeidel username: ").strip()
        password = getpass.getpass("MySpeidel password: ")
        token = login(username, password)
        client = MySpeidelClient(token=token)
        recipes = private_recipes(client, machine_size=args.machine_size)
        if not recipes:
            print("No private recipes found for the selected machine size.")
            return 0
        print(f"Found {len(recipes)} private recipes for {args.machine_size} L.")
        print("Select one by number (no names or UUIDs printed):")
        for index in range(1, len(recipes) + 1):
            print(f"  {index}")
        choice = input("Recipe number (Enter to cancel): ").strip()
        if not choice:
            print("Cancelled; no detail fetched.")
            return 0
        if not choice.isascii() or not choice.isdecimal():
            raise MySpeidelError("Invalid selection")
        selected = int(choice)
        if not 1 <= selected <= len(recipes):
            raise MySpeidelError("Selection out of range")
        structure = inspect_recipe(client, recipes[selected - 1], machine_size=args.machine_size)
        result = {"cloud": structure, "local": local_recipe_inventory(args.local_recipe)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("PASS: read-only recipe inspection; no recipe values exported")
        return 0
    except (MySpeidelError, RecipeError, OSError, EOFError, KeyboardInterrupt, ValueError):
        print("ERROR: Recipe inspection failed (no credential or recipe content displayed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
