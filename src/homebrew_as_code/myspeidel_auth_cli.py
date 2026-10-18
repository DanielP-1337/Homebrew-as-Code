"""One-shot MySpeidel login and read-only recipe schema test.

Password entered via getpass; neither password nor returned token is printed.
"""
import argparse
import getpass
import json
import sys

from .myspeidel import MySpeidelClient, MySpeidelError, inspect_structure
from .myspeidel_auth import login


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-shot MySpeidel authenticated read-only check")
    parser.add_argument("--username", help="Account username (omit to enter interactively)")
    parser.add_argument("--machine-size", type=int, default=20)
    args = parser.parse_args(argv)
    try:
        username = args.username or input("MySpeidel username: ").strip()
        password = getpass.getpass("MySpeidel password: ")
        if not password:
            raise MySpeidelError("Password is required")
        token = login(username, password)
        client = MySpeidelClient(token=token)
        recipes = client.list_recipes(machine_size=args.machine_size)
        print("PASS: MySpeidel authentication and read-only recipe listing")
        print(json.dumps(inspect_structure(recipes), ensure_ascii=False, indent=2))
        return 0
    except (MySpeidelError, EOFError, KeyboardInterrupt):
        print("ERROR: MySpeidel login or recipe read failed (no credentials displayed)", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
