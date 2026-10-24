"""Produce three separate, offline procurement requests (no network)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .recipe import load_recipe
from .supplier_split import render_split


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Split recipe into brewshop, grocery and water chemistry requests')
    parser.add_argument('recipe')
    parser.add_argument('--catalog', default='catalogs/braupartner.verified.yaml')
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args(argv)
    try:
        catalog = yaml.safe_load(Path(args.catalog).read_text(encoding='utf-8'))
        rendered = render_split(load_recipe(args.recipe), catalog)
        outputs = {Path(args.output_prefix + suffix): content for suffix, content in rendered.items()}
        if any(p.exists() for p in outputs):
            raise ValueError('Refusing to overwrite existing output files')
        # Verify calculations and output paths before writing any file.
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        for path, content in outputs.items():
            path.write_text(content, encoding='utf-8')
            print('OFFLINE SPLIT FILE: ' + str(path))
        print('REQUESTS ONLY. No purchase order, checkout or email sent.')
        return 0
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        print('ERROR: supplier split failed: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
