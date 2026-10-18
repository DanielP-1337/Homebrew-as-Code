"""Read-only API discovery CLI; does not save customer data to disk."""

import argparse
import json
import sys

from .myspeidel import MySpeidelClient, MySpeidelError, inspect_structure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MySpeidel read-only API discovery")
    sub = parser.add_subparsers(dest="command", required=True)
    recipes = sub.add_parser("list", help="Read recipe metadata (prints schema only by default)")
    recipes.add_argument("--machine-size", type=int, default=20)
    recipes.add_argument("--include-public", action="store_true")
    recipe = sub.add_parser("get", help="Read an individual recipe by numeric ID")
    recipe.add_argument("uuid")
    args = parser.parse_args(argv)
    try:
        client = MySpeidelClient()
        result = (client.list_recipes(machine_size=args.machine_size, include_public=args.include_public)
                  if args.command == "list" else client.get_recipe(args.uuid))
        print(json.dumps(inspect_structure(result), indent=2, ensure_ascii=False))
        return 0
    except MySpeidelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
