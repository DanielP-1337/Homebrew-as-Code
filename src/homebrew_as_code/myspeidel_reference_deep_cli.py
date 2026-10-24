"""CLI for local, read-only inspection of MySpeidel's OpenAPI example/schema."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .myspeidel_reference_deep import inspect_deep_files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deep-inspect locally downloaded MySpeidel recipe_v5 OpenAPI")
    parser.add_argument("recipe")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        path = Path(args.output)
        if path.exists():
            raise ValueError("Refusing to overwrite output")
        report = inspect_deep_files(args.spec, args.recipe)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2, allow_nan=False)
            fh.write("\n")
        print("OFFLINE DEEP INSPECTION: " + str(path))
        print("Required fields: " + str(len(report["required_top_level"])))
        print("Example missing required: " + str(len(report["example_missing_required"])))
        print("NO UPLOAD / NO API CALLS / NO VENDOR SAMPLE DATA EXPORTED")
        return 0
    except (ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
