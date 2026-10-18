"""Resolve a reviewable, private supplier catalog into 0011 mapping and report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .recipe import load_recipe
from .supplier_catalog import resolve_catalog


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline supplier package resolution; no network or checkout')
    parser.add_argument('recipe')
    parser.add_argument('--source', required=True, help='Locally reviewed supplier catalog YAML')
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args(argv)
    try:
        prefix = Path(args.output_prefix)
        mapping_file = Path(str(prefix) + '.catalog.yaml')
        report_file = Path(str(prefix) + '.catalog-report.json')
        if mapping_file.exists() or report_file.exists():
            raise ValueError('Refusing to overwrite existing outputs')
        source = yaml.safe_load(Path(args.source).read_text(encoding='utf-8'))
        mapping, report = resolve_catalog(load_recipe(args.recipe), source)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        mapping_file.write_text(yaml.safe_dump(mapping, allow_unicode=True, sort_keys=True), encoding='utf-8')
        report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
        print('OFFLINE CATALOG: ' + str(mapping_file))
        print('REVIEW REPORT: ' + str(report_file))
        print('Cart fully resolved: ' + str(report['cart_ready']))
        return 0
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print('ERROR: catalog resolution failed: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
