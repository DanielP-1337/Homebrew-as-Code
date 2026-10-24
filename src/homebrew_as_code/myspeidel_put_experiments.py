"""Opt-in PUT compatibility experiments on a backed-up private test recipe.

Never changes the input backup. No network activity in preparation mode.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

from .myspeidel_put_roundtrip import (
    PutDiagnosticError, check_private, digest, private_file, put_recipe, read_backup, write_new,
)

FORMAT = 'homebrew-as-code/myspeidel-put-experiment-v1'
VARIANTS = ('original', 'omit-null-names', 'empty-string-names')
CATEGORIES = ('water_types', 'hops')


def make_variant(recipe: dict[str, Any], variant: str) -> tuple[dict[str, Any], dict[str, int]]:
    """Copy only known reference entries; preserve keys and all other fields."""
    if variant not in VARIANTS:
        raise ValueError('Unknown experiment variant')
    candidate = copy.deepcopy(recipe)
    counts = {category: 0 for category in CATEGORIES}
    if variant == 'original':
        return candidate, counts
    references = candidate.get('references')
    if not isinstance(references, dict):
        raise ValueError('Missing references object')
    for category in CATEGORIES:
        entries = references.get(category)
        if not isinstance(entries, dict):
            raise ValueError('Missing or invalid reference category')
        for entry in entries.values():
            if not isinstance(entry, dict):
                raise ValueError('Invalid reference entry')
            if 'name' in entry and entry['name'] is None:
                counts[category] += 1
                if variant == 'omit-null-names':
                    del entry['name']
                else:
                    entry['name'] = ''
    if not any(counts.values()):
        raise ValueError('No matching null names; refusing a no-op experiment')
    return candidate, counts


def offline_check(spec_path: str, recipe: dict[str, Any]) -> list[dict[str, Any]]:
    """Value-free schema counts. These checks are not proof of server acceptance."""
    from .myspeidel_golden_validation import _issues
    path = private_file(spec_path, must_exist=True)
    if path.stat().st_size > 10_000_000:
        raise ValueError('Oversized OpenAPI spec')
    spec = json.loads(path.read_text(encoding='utf-8'))
    schemas = spec['components']['schemas']
    result = []
    for version in ('recipe_v4', 'recipe_v5'):
        errors, unverified = _issues(spec, schemas[version], recipe, '$')
        result.append({'schema': version, 'errors': len(errors), 'unverified': len(unverified)})
    return result


def _current(client: Any, uuid: str) -> dict[str, Any]:
    return check_private(client.get_recipe(uuid), uuid)


def _write_receipt(marker_path: Path, receipt: dict[str, Any]) -> None:
    """Atomically publish a value-free receipt; never overwrite the attempt marker."""
    receipt_path = marker_path.with_name(marker_path.name + '.receipt.json')
    temp_path = receipt_path.with_name(receipt_path.name + '.pending')
    # Exclusive creation prevents accidentally replacing an older receipt.
    with temp_path.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    # The receipt filename is reserved via exclusive creation rather than a
    # destructive replace. The temporary file remains if publishing fails.
    try:
        os.link(temp_path, receipt_path)
    finally:
        if receipt_path.exists():
            temp_path.unlink(missing_ok=True)


def _run_online(args: Any, uuid: str, baseline: dict[str, Any], baseline_sha: str,
                candidate: dict[str, Any], variant_sha: str) -> None:
    marker_path = private_file(args.result)
    write_new(marker_path, {
        'format': FORMAT, 'phase': 'attempt_started', 'variant': args.variant,
        'mode': args.mode, 'baseline_sha256': baseline_sha,
        'candidate_sha256': variant_sha,
        'status': 'indeterminate_until_verified',
    })
    receipt: dict[str, Any] = {
        'format': FORMAT, 'variant': args.variant, 'mode': args.mode,
        'phase': 'preflight', 'http_status': None, 'error_type': None,
        'error_location': None, 'server_state': 'not_checked',
        'put_outcome': 'not_sent',
    }
    sent = False
    try:
        from .myspeidel_put_roundtrip_cli import _login
        token, client = _login()
        if digest(_current(client, uuid)) != baseline_sha:
            raise ValueError('Current server state differs from backup; request NOT sent')
        phrase = ('DRY RUN EXPERIMENT' if args.mode == 'dry-run'
                  else 'WRITE TEST RECIPE')
        response = input(f'Type {phrase} to authorize this PUT: ')
        if response != phrase:
            raise ValueError('Consent not given; request NOT sent')
        print('Attempt marker saved; server request will now be sent. Do not blindly retry.')
        sent = True  # Includes an uncertain network failure before sending bytes.
        receipt['put_outcome'] = 'indeterminate'
        receipt['phase'] = 'request_started'
        try:
            status = put_recipe(token, uuid, candidate, dry_run=args.mode == 'dry-run')
            receipt.update(phase='put_accepted', put_outcome='accepted', http_status=status)
            print(f'PUT HTTP {status}')
        except PutDiagnosticError as exc:
            # Only explicitly enumerated, application-owned category/location tokens.
            categories = {'schema_validation', 'unclassified', 'other_error', 'server_error'}
            locations = {'unknown', 'uuid', 'public', 'recipe_type', 'water_plato',
                         'machine_type', 'owner', 'brewer', 'mashing', 'rest', 'boil',
                         'fermentation', 'maturation', 'references'}
            if isinstance(getattr(exc, 'validation_details', None), dict):
                receipt['validation_details'] = exc.validation_details
            receipt.update(phase='put_rejected', put_outcome='rejected',
                           http_status=exc.status if type(exc.status) is int else None,
                           error_type=exc.category if exc.category in categories else 'unclassified',
                           error_location=exc.location if exc.location in locations else 'unknown')
            raise
        finally:
            # A request failure may still have committed. Never suppress the PUT error.
            try:
                current_sha = digest(_current(client, uuid))
                if current_sha == baseline_sha:
                    receipt['server_state'] = 'baseline_match'
                    print('GET after attempt: baseline digest MATCH')
                elif current_sha == variant_sha:
                    receipt['server_state'] = 'candidate_match'
                    print('GET after attempt: candidate digest MATCH')
                else:
                    receipt['server_state'] = 'different'
                    print('GET after attempt: digest differs from both baseline and candidate')
            except Exception:
                receipt['server_state'] = 'unavailable'
                print('GET after attempt: unavailable; server state INDETERMINATE')
        if args.mode == 'apply':
            print('REAL PUT attempted. Backup remains untouched; restore requires a separate confirmed operation.')
    finally:
        # If the PUT threw an unexpected exception, avoid claiming it was rejected.
        if sent and receipt['phase'] == 'request_started':
            receipt['phase'] = 'request_failed'
        _write_receipt(marker_path, receipt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='MySpeidel controlled PUT compatibility experiments')
    parser.add_argument('--backup', required=True, help='Existing .local backup file')
    parser.add_argument('--variant', choices=VARIANTS, required=True)
    parser.add_argument('--mode', choices=('prepare', 'dry-run', 'apply'), default='prepare')
    parser.add_argument('--spec', help='Existing .local OpenAPI JSON (prepare only)')
    parser.add_argument('--result', required=True, help='Fresh .local output path (never overwritten)')
    parser.add_argument('--allow-live-write', action='store_true',
                        help='Required for a real PUT with dryRun=0')
    args = parser.parse_args(argv)
    try:
        uuid, baseline, baseline_sha = read_backup(private_file(args.backup, must_exist=True))
        check_private(baseline, uuid)
        candidate, counts = make_variant(baseline, args.variant)
        check_private(candidate, uuid)
        candidate_sha = digest(candidate)
        if digest(baseline) != baseline_sha:
            raise ValueError('Backup changed during preparation')
        if args.mode == 'prepare':
            result = {
                'format': FORMAT, 'offline': True, 'variant': args.variant,
                'baseline_sha256': baseline_sha, 'candidate_sha256': candidate_sha,
                'changes_by_reference_category': counts,
                'supported_schema_checks': offline_check(args.spec, candidate) if args.spec else None,
                'upload_ready': False,
            }
            write_new(private_file(args.result), result)
            print('OFFLINE report written under .local; no HTTP and no recipe modification.')
        else:
            if args.spec:
                raise ValueError('--spec is valid only for prepare')
            if args.mode == 'apply' and not args.allow_live_write:
                raise ValueError('Real PUT requires --allow-live-write')
            _run_online(args, uuid, baseline, baseline_sha, candidate, candidate_sha)
        return 0
    except Exception as exc:
        # Avoid leaking server messages, recipe IDs, paths, or credentials.
        print('Experiment stopped: ' + (str(exc) if isinstance(exc, ValueError) and
              str(exc) in {
                  'Current server state differs from backup; request NOT sent',
                  'Consent not given; request NOT sent',
                  'Real PUT requires --allow-live-write',
                  'No matching null names; refusing a no-op experiment',
                  'Backup changed during preparation',
              } else type(exc).__name__), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
