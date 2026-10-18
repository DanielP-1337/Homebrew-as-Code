"""Offline, source-attributed Braupartner offer report; no network."""
import argparse
import json
import sys
from pathlib import Path
import yaml
from .recipe import load_recipe
from .supplier_evidence import audit_offers


def main(argv=None):
    parser = argparse.ArgumentParser(description='Audit sourced supplier offers offline; never place orders')
    parser.add_argument('recipe')
    parser.add_argument('--catalog', default='catalogs/braupartner.verified.yaml')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        dest = Path(args.output)
        if dest.exists():
            raise ValueError('Refusing overwrite')
        source = yaml.safe_load(Path(args.catalog).read_text(encoding='utf-8'))
        report = audit_offers(load_recipe(args.recipe), source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
        print(f'OFFLINE EVIDENCE REPORT: {dest}')
        print(f'Documented offers: {sum(x["offer_type"] != "UNRESOLVED" for x in report["rows"])} / {len(report["rows"])}')
        print('No merchant product IDs or checkout permissions inferred.')
        return 0
    except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
