"""Opt-in GET of one private test recipe; later manual reference confirmation."""
from __future__ import annotations
import argparse
import getpass
import json
import sys
from pathlib import Path
import yaml
from .myspeidel import MySpeidelClient
from .myspeidel_auth import login
from .myspeidel_inspect import private_recipes
from .myspeidel_private_references import extract_observations, confirm_observations
from .recipe import load_recipe


def _private_path(value: str) -> Path:
    dest = Path(value)
    if '.local' not in dest.parts:
        raise ValueError('Output must be inside .local')
    if dest.exists():
        raise ValueError('Refusing to overwrite')
    return dest


def main(argv=None):
    parser = argparse.ArgumentParser(description='GET-only reference observations or offline manual confirmation')
    sub = parser.add_subparsers(dest='mode', required=True)
    fetch = sub.add_parser('fetch')
    fetch.add_argument('--output', required=True)
    confirm = sub.add_parser('confirm')
    confirm.add_argument('recipe')
    confirm.add_argument('--observations', required=True)
    confirm.add_argument('--decisions', required=True)
    confirm.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        dest = _private_path(args.output)
        if args.mode == 'fetch':
            print('GET-only: select an existing private 20 L reference recipe. No cloud writes.')
            username = input('MySpeidel username: ').strip()
            password = getpass.getpass('MySpeidel password: ')
            client = MySpeidelClient(token=login(username,password))
            recipes = private_recipes(client, machine_size=20)
            for i in range(len(recipes)):
                print(f'  {i+1} (name hidden)')
            choice = input('Reference recipe number (Enter cancels): ').strip()
            if not choice:
                return 0
            if not choice.isascii() or not choice.isdecimal() or not 1 <= int(choice) <= len(recipes):
                raise ValueError('Invalid selection')
            if input('Read ONLY this private recipe and store UUID observations under .local? [yes/NO]: ').strip() != 'yes':
                return 0
            item = recipes[int(choice)-1]
            detail = client.get_recipe(item['uuid'])
            if not isinstance(detail, dict) or detail.get('public') not in (0,False) or detail.get('uuid') != item['uuid']:
                raise ValueError('Private recipe identity check failed')
            print('\nMySpeidel recipe_v5 reference fields:')
            for field in ('public', 'recipe_type', 'water_plato'):
                value = detail.get(field, '<MISSING>')
                print(f'  {field}: {value!r}')
            output = extract_observations(detail)
            payload = json.dumps(output,indent=2,ensure_ascii=False)+'\n'
            count = len(output['observations'])
        else:
            observed = json.loads(Path(args.observations).read_text(encoding='utf-8'))
            decisions = yaml.safe_load(Path(args.decisions).read_text(encoding='utf-8'))
            output = confirm_observations(load_recipe(args.recipe), observed, decisions)
            payload = yaml.safe_dump(output,allow_unicode=True,sort_keys=False)
            count = len(output['entries'])
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(payload,encoding='utf-8')
        print('PRIVATE OUTPUT: '+str(dest))
        print(f'Entries: {count}; no recipe write or upload')
        return 0
    except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError, json.JSONDecodeError, EOFError, KeyboardInterrupt):
        print('ERROR: reference extraction/confirmation failed (private details suppressed)',file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
