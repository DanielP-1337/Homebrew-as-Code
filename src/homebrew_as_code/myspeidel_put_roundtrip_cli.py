"""User-approved backup -> PUT dry-run -> PUT apply workflow (no silent writes)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .myspeidel import MySpeidelClient, MySpeidelError
from .myspeidel_auth import login
from .myspeidel_credentials import CredentialStoreError, prompt_credentials
from .myspeidel_inspect import private_recipes
from .myspeidel_put_roundtrip import (PutDiagnosticError, check_private, digest, private_file,
                                     put_recipe, read_backup, write_new)


def _login():
    user, secret = prompt_credentials()
    token = login(user, secret)
    return token, MySpeidelClient(token=token)


def _same(client, uuid, baseline):
    current = check_private(client.get_recipe(uuid), uuid)
    if digest(current) != baseline:
        raise ValueError('Server recipe differs from saved baseline; no write permitted')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Controlled private MySpeidel recipe PUT test')
    sub = parser.add_subparsers(dest='action', required=True)
    backup = sub.add_parser('backup', help='Only GET and write local private backup')
    backup.add_argument('--output', required=True)
    verify = sub.add_parser('verify', help='Read-only GET comparison against existing backup')
    verify.add_argument('--backup', required=True)
    dry = sub.add_parser('dry-run', help='PUT dryRun only, with GET verification')
    dry.add_argument('--backup', required=True)
    dry.add_argument('--receipt', required=True)
    apply = sub.add_parser('apply', help='REAL PUT; requires dry-run receipt and manual consent')
    apply.add_argument('--backup', required=True)
    apply.add_argument('--receipt', required=True)
    apply.add_argument('--result', required=True)
    offline = sub.add_parser('offline-schema', help='Compare private backup with v4/v5 locally; no login or HTTP')
    offline.add_argument('--backup', required=True)
    offline.add_argument('--spec', required=True)
    offline.add_argument('--report', required=True)
    args = parser.parse_args(argv)
    phase = 'setup'
    try:
        if args.action == 'offline-schema':
            from .myspeidel_put_offline_schema import compare_backup
            destination = private_file(args.report)
            report = compare_backup(args.spec, args.backup)
            write_new(destination, report)
            for result in report['results']:
                print(f"{result['schema']}: errors={result['error_count']}; "
                      f"unverified={result['unverified_count']}")
                for conflict in result['type_conflicts']:
                    print(f"  type_conflict[{conflict['index']}]: path={conflict['path']}; "
                          f"expected={conflict['expected']}; actual={conflict['actual']}; "
                          f"nullable={conflict['nullable']}")
            print('OFFLINE only; report saved under .local; no login or HTTP.')
            return 0
        if args.action == 'backup':
            output = private_file(args.output)
            phase = 'login'
            _, client = _login()
            recipes = private_recipes(client, machine_size=20)
            print(f'Found {len(recipes)} private 20 L recipes (names hidden).')
            for idx in range(len(recipes)):
                print(f'  {idx + 1} (name hidden)')
            choice = input('Select recipe number (Enter cancels): ').strip()
            if not choice:
                return 0
            if not choice.isascii() or not choice.isdecimal() or int(choice) not in range(1, len(recipes)+1):
                raise ValueError('Invalid recipe selection')
            if input('Save FULL private GET recipe locally? [yes/NO]: ').strip() != 'yes':
                return 0
            uuid = recipes[int(choice)-1]['uuid']
            phase = 'backup_get'
            recipe = check_private(client.get_recipe(uuid), uuid)
            write_new(output, {'format': 'homebrew-as-code/myspeidel-put-backup-v1',
                               'uuid': uuid, 'recipe': recipe, 'sha256': digest(recipe)})
            print('Private backup saved; NO API writes.')
            return 0

        phase = 'backup_validation'
        backup_path = private_file(args.backup, must_exist=True)
        uuid, recipe, sha = read_backup(backup_path)
        phase = 'login'
        token, client = _login()
        phase = 'preflight_get'
        _same(client, uuid, sha)
        if args.action == 'verify':
            print('READ-ONLY verification PASS: server recipe matches backup; no PUT sent.')
            return 0
        if args.action == 'dry-run':
            receipt_path = private_file(args.receipt)
            if input('Perform PUT dryRun=1 on this existing PRIVATE recipe? [yes/NO]: ').strip() != 'yes':
                return 0
            phase = 'dry_run_put'
            put_recipe(token, uuid, recipe, dry_run=True)
            phase = 'post_dry_run_get'
            _same(client, uuid, sha)  # No observed side effect on GET data
            phase = 'receipt_write'
            write_new(receipt_path, {'format': 'homebrew-as-code/myspeidel-put-dry-run-v1',
                                     'uuid': uuid, 'sha256': sha, 'http_status': 200,
                                     'after_get_identical': True})
            print('Dry-run HTTP 200; GET snapshot identical. Receipt saved.')
            return 0

        phase = 'apply_receipt_validation'
        receipt_path = private_file(args.receipt, must_exist=True)
        result_path = private_file(args.result)
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if (not isinstance(receipt, dict) or receipt.get('format') != 'homebrew-as-code/myspeidel-put-dry-run-v1'
                or receipt.get('uuid') != uuid or receipt.get('sha256') != sha
                or receipt.get('http_status') != 200 or receipt.get('after_get_identical') is not True):
            raise ValueError('No matching, successful dry-run receipt')
        print('WARNING: REAL PUT may change update_on, content_version or other server fields.')
        print('This operation updates the EXISTING private 20 L recipe using the exact saved GET payload.')
        if input('Type exactly WRITE PRIVATE RECIPE to proceed: ').strip() != 'WRITE PRIVATE RECIPE':
            print('Cancelled; no PUT.')
            return 0
        phase = 'pre_apply_get'
        _same(client, uuid, sha)
        # Create evidence marker BEFORE network send, so interrupted/failed PUT
        # cannot be blindly retried using the same --result path.
        phase = 'apply_marker_write'
        write_new(result_path, {'format': 'homebrew-as-code/myspeidel-put-attempt-v1',
                                'uuid': uuid, 'baseline_sha256': sha,
                                'status': 'ATTEMPTED_CHECK_SERVER_BEFORE_RETRY'})
        phase = 'apply_put'
        put_recipe(token, uuid, recipe, dry_run=False)
        phase = 'post_apply_get'
        after = check_private(client.get_recipe(uuid), uuid)
        print('REAL PUT HTTP 200. Post-PUT GET completed.')
        print('Same JSON as baseline:', digest(after) == sha)
        print('Attempt marker saved; do not automatically retry or overwrite the original backup.')
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError, MySpeidelError, EOFError, KeyboardInterrupt) as exc:
        # All printed values are internal enums or integer HTTP status.
        # NEVER interpolate arbitrary exceptions, response bodies, or server text.
        if phase in ('dry_run_put', 'apply_put') and isinstance(exc, PutDiagnosticError):
            status = f'; HTTP {exc.status}' if isinstance(exc.status, int) else ''
            print(f'ERROR: phase={phase}{status}; category={exc.category}; '
                  f'location={exc.location}; private details suppressed. '
                  'Do not blindly retry PUT.', file=sys.stderr)
            for path in exc.paths:
                print(f'  validation_path={path}', file=sys.stderr)
        else:
            print(f'ERROR: phase={phase}; details suppressed. Do not blindly retry PUT.',
                  file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
