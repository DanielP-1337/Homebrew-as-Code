"""Interactive, one-shot and read-only MySpeidel numeric semantics inspector."""
from __future__ import annotations

import argparse
import getpass
import json
import sys

from .myspeidel import MySpeidelClient, MySpeidelError
from .myspeidel_auth import login
from .myspeidel_inspect import private_recipes
from .myspeidel_semantics import analyze_detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect MySpeidel numeric fields (read-only)")
    parser.add_argument("--machine-size", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        if args.machine_size <= 0:
            raise MySpeidelError("Invalid machine size")
        username = input("MySpeidel username: ").strip()
        password = getpass.getpass("MySpeidel password: ")
        client = MySpeidelClient(token=login(username, password))
        recipes = private_recipes(client, machine_size=args.machine_size)
        if not recipes:
            print("No matching private recipes.")
            return 0
        print(f"Found {len(recipes)} private recipes for {args.machine_size} L.")
        for number in range(1, len(recipes) + 1):
            print(f"  {number}")
        choice = input("Recipe number (Enter to cancel): ").strip()
        if not choice:
            print("Cancelled.")
            return 0
        if not choice.isascii() or not choice.isdecimal() or not 1 <= int(choice) <= len(recipes):
            raise MySpeidelError("Invalid selection")
        consent = input("Print selected recipe's numeric ingredient amounts and step times? [yes/NO]: ").strip()
        if consent != "yes":
            print("Cancelled before fetching recipe details.")
            return 0
        selected = recipes[int(choice) - 1]
        detail = client.get_recipe(selected["uuid"])
        # Verify the detail's machine size independently before disclosing values.
        if not isinstance(detail, dict) or not isinstance(detail.get("machine_type"), dict) or detail["machine_type"].get("size") != args.machine_size:
            raise MySpeidelError("Detail machine size could not be verified")
        print(json.dumps(analyze_detail(detail), indent=2, ensure_ascii=False, allow_nan=False))
        print("PASS: GET-only numeric inspection; no IDs, names or token displayed")
        return 0
    except (MySpeidelError, EOFError, KeyboardInterrupt, ValueError, TypeError):
        print("ERROR: Recipe semantics inspection failed (private details suppressed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
