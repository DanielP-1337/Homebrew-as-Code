"""One-shot, read-only browser-to-API timing comparison. No disk export."""
from __future__ import annotations

import argparse
import getpass
import json
import re
import sys

from .myspeidel import MySpeidelClient, MySpeidelError
from .myspeidel_auth import login
from .myspeidel_inspect import private_recipes
from .myspeidel_roundtrip import compare_roundtrip, parse_web_times


def _display_meta(value: object, *, limit: int = 80) -> str:
    """One terminal-safe line; never render ANSI/control codes from API metadata."""
    if not isinstance(value, str) or not value.strip():
        return "(unknown)"
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", value)
    cleaned = " ".join(cleaned.split())
    return cleaned[:limit] if cleaned else "(unknown)"


def _creation_date(meta: dict) -> str:
    """Use only the date portion of a recognized ISO date, no arbitrary text."""
    value = meta.get("created_on")
    if not isinstance(value, str):
        return "(unknown)"
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})(?:[T ].*)?", value)
    return match.group(1) if match else "(unknown)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare manual MySpeidel web times with GET-only API times")
    parser.add_argument("--machine-size", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        if args.machine_size <= 0:
            raise MySpeidelError("Invalid machine size")
        print("Create a PRIVATE test recipe manually via MySpeidel web UI first.")
        print("This tool ONLY reads an existing selected recipe; it cannot create or change recipes.")
        username = input("MySpeidel username: ").strip()
        password = getpass.getpass("MySpeidel password: ")
        client = MySpeidelClient(token=login(username, password))
        recipes = private_recipes(client, machine_size=args.machine_size)
        if not recipes:
            print("No matching private recipes.")
            return 0
        print(f"Found {len(recipes)} private recipes for {args.machine_size} L.")
        print("Order is returned by the API; it is NOT guaranteed to be stable.")
        reveal = input("Show private recipe names and creation dates on screen? [yes/NO]: ").strip() == "yes"
        for index, recipe in enumerate(recipes, 1):
            if reveal:
                print(f"  {index}  {_display_meta(recipe.get('name'))}  [{_creation_date(recipe)}]")
            else:
                print(f"  {index}")
        choice = input("Test recipe number (Enter to cancel): ").strip()
        if not choice:
            print("Cancelled.")
            return 0
        if not choice.isascii() or not choice.isdecimal() or not 1 <= int(choice) <= len(recipes):
            raise MySpeidelError("Invalid recipe selection")
        total = float(input("Total boil duration in WEB form (minutes): ").strip())
        times = parse_web_times(input("WEB hop times (minutes BEFORE end, descending, comma-separated): "), total)
        consent = input("GET selected recipe and print NUMERIC comparison? [yes/NO]: ").strip()
        if consent != "yes":
            print("Cancelled before recipe detail GET.")
            return 0
        detail = client.get_recipe(recipes[int(choice) - 1]["uuid"])
        if not isinstance(detail, dict) or not isinstance(detail.get("machine_type"), dict) or detail["machine_type"].get("size") != args.machine_size:
            raise MySpeidelError("Recipe detail machine type mismatch")
        result = compare_roundtrip(detail, total, times)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        print("PASS: GET-only; numeric-only; no UUID, name, token or raw recipe printed")
        return 0
    except (MySpeidelError, ValueError, TypeError, EOFError, KeyboardInterrupt):
        print("ERROR: Roundtrip comparison failed (private details suppressed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
