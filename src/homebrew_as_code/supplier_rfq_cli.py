"""Offline supplier email-attachment packet; never contacts supplier."""
import argparse
import sys
from pathlib import Path

import yaml

from .recipe import load_recipe
from .supplier_rfq import render_rfq


def main(argv=None):
    parser = argparse.ArgumentParser(description='Generate offline RFQ JSON, CSV, Markdown and review report')
    parser.add_argument('recipe')
    parser.add_argument('--catalog', default='catalogs/braupartner.verified.yaml')
    parser.add_argument('--output-prefix', required=True)
    args = parser.parse_args(argv)
    try:
        catalog = yaml.safe_load(Path(args.catalog).read_text(encoding='utf-8'))
        docs = render_rfq(load_recipe(args.recipe), catalog)
        outputs = {Path(args.output_prefix + ext): content for ext, content in docs.items()}
        if len(outputs) != len(docs) or any(p.exists() for p in outputs):
            raise ValueError('Refusing to overwrite RFQ outputs')
        # Validate all renderings before writing anything.
        for p in outputs:
            p.parent.mkdir(parents=True, exist_ok=True)
        written = []
        try:
            for p, content in outputs.items():
                with p.open('x', encoding='utf-8', newline='') as f:
                    f.write(content)
                written.append(p)
        except Exception:
            for p in written:
                p.unlink(missing_ok=True)
            raise
        for p in outputs:
            print('RFQ FILE: ' + str(p))
        print('RFQ ONLY. No order placed or sent.')
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print('ERROR: RFQ generation failed: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
