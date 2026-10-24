"""Offline-only golden reference candidate and structural validation report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .myspeidel_golden_validation import build_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline reference validation; never submit')
    parser.add_argument('--spec', required=True)
    parser.add_argument('--candidate', required=True, help='Private output, must live under .local')
    parser.add_argument('--report', required=True, help='Sanitized report output')
    args = parser.parse_args(argv)
    try:
        root = Path.cwd().resolve()
        private = (root / '.local').resolve()
        candidate = Path(args.candidate).resolve()
        report_path = Path(args.report).resolve()
        if not candidate.is_relative_to(private):
            raise ValueError('Candidate must be inside repository .local directory')
        if candidate == report_path or candidate.exists() or report_path.exists():
            raise ValueError('Output exists or output paths overlap; refusing overwrite')
        obj, report = build_file(args.spec)
        candidate.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with candidate.open('x', encoding='utf-8') as stream:
            json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        with report_path.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        print('OFFLINE: private candidate saved under .local; not upload-ready')
        print(f'Validation report: {report_path}')
        print(f'Schema errors: {len(report["schema_errors"])}; unverified constraints: {len(report["unverified_constraints"])}')
        print('No cloud access, no recipe write or upload')
        return 0 if report['schema_check_passed'] else 2
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print('ERROR: local reference validation failed: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
