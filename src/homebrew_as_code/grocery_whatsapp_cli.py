"""Write a WhatsApp-ready grocery list; user copies and sends manually."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .grocery_whatsapp import render_whatsapp
from .recipe import load_recipe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline grocery WhatsApp text; no messages sent')
    parser.add_argument('recipe')
    parser.add_argument('--catalog', default='catalogs/braupartner.verified.yaml')
    parser.add_argument('--output', required=True, help='New .txt file (will not overwrite)')
    args = parser.parse_args(argv)
    try:
        target = Path(args.output)
        if target.suffix.lower() != '.txt':
            raise ValueError('output must have .txt extension')
        source = yaml.safe_load(Path(args.catalog).read_text(encoding='utf-8'))
        message = render_whatsapp(load_recipe(args.recipe), source)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents overwrites even on repeated invocations.
        with target.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(message)
        print('WHATSAPP TEXT (not sent): ' + str(target))
        print('Copy manually using Get-Content -Raw | Set-Clipboard and paste in WhatsApp.')
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print('ERROR: grocery export failed: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
