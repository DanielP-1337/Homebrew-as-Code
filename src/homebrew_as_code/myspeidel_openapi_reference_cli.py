"""Offline MySpeidel OpenAPI reference inventory; no API calls."""
import argparse
import json
import sys
from pathlib import Path

from .myspeidel_openapi_reference import inspect_files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect locally saved MySpeidel OpenAPI 3.x specification offline")
    parser.add_argument("recipe", help="Local Homebrew-as-Code YAML recipe")
    parser.add_argument("--spec", required=True, help="Downloaded official JSON OpenAPI specification")
    parser.add_argument("--output", required=True, help="Local report path (must not exist)")
    args = parser.parse_args(argv)
    try:
        target = Path(args.output)
        if target.exists():
            raise ValueError("Refusing to overwrite an existing report")
        report = inspect_files(args.spec, args.recipe)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        print("OFFLINE OpenAPI reference report: " + str(target))
        print(f"Recipe v5 fields: {len(report['fields'])}; required: {len(report['api_required_fields'])}")
        print("NO PAYLOAD / NO NETWORK / NO CLOUD WRITE")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
