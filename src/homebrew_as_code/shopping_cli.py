"""Offline RFQ export for possible Shopware 6 merchants."""
import argparse
import sys
from pathlib import Path
from .shopping_export import export_file


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline RFQ JSON/CSV and Shopware cart preview; no network')
    parser.add_argument('recipe')
    parser.add_argument('--output-prefix', required=True)
    parser.add_argument('--catalog', help='Private local YAML mapping of merchant product IDs')
    args = parser.parse_args(argv)
    try:
        outputs = [Path(args.output_prefix + suffix) for suffix in ('.rfq.json', '.rfq.csv', '.shopware-cart-preview.json')]
        if any(path.exists() for path in outputs):
            raise ValueError('Refusing to overwrite existing export files')
        contents = export_file(args.recipe, catalog_path=args.catalog)
        for path in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
        for path, content in zip(outputs, contents):
            path.write_text(content, encoding='utf-8')
        print('RFQ ONLY: ' + str(outputs[0]))
        print('HUMAN CSV: ' + str(outputs[1]))
        print('OFFLINE SHOPWARE PREVIEW: ' + str(outputs[2]))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ERROR: export failed: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
