"""Offline manufacturer reference inspection; no HTTP functions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .myspeidel_golden_reference import inspect_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Inspect local MySpeidel reference; never upload')
    parser.add_argument('--spec', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        dest = Path(args.output)
        if dest.exists():
            raise ValueError('Refusing to overwrite existing report')
        report = inspect_file(args.spec)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
        print('OFFLINE GOLDEN REFERENCE REPORT: ' + str(dest))
        print('Example missing required: ' + str(len(report['example_missing_required'])))
        print('No upload payload or network operations')
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print('ERROR: reference analysis failed: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
