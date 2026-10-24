"""Controlled roundtrip on a personally owned COPY of an official recipe.

The webpage's numeric ID is not an API UUID. Use the existing GET-only backup
command to select a private recipe after copying it in MySpeidel's web UI.
"""
from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace

from .myspeidel_put_roundtrip import check_private, digest, private_file, read_backup, write_new

SOURCE_URL = 'https://www.myspeidel.com/recipes/view_recipe/2054'
FORMAT = 'homebrew-as-code/myspeidel-official-golden-roundtrip-v1'


def validate_copy(backup_path: str, confirmed: bool):
    """Confirm an owned private 20 L copy; never infer ownership from a URL."""
    if not confirmed:
        raise ValueError('Explicit --confirm-private-copy is required')
    uuid, recipe, sha = read_backup(private_file(backup_path, must_exist=True))
    check_private(recipe, uuid)
    name = recipe.get('name')
    if not isinstance(name, str) or 'weizenbier' not in name.casefold() or '38' not in name:
        raise ValueError('Backup name does not identify the expected Weizenbier 38 copy')
    if digest(recipe) != sha:
        raise ValueError('Backup digest mismatch')
    return uuid, recipe, sha


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Official Speidel recipe copy: private GET -> PUT roundtrip')
    parser.add_argument('--backup', required=True, help='Existing private GET backup under .local')
    parser.add_argument('--mode', choices=('prepare', 'dry-run', 'apply'), default='prepare')
    parser.add_argument('--result', required=True, help='New output marker under .local')
    parser.add_argument('--spec', help='OpenAPI spec for offline checks, prepare only')
    parser.add_argument('--confirm-private-copy', action='store_true', help='Attest recipe is your own private copy')
    parser.add_argument('--allow-live-write', action='store_true', help='Additional opt-in for dryRun=0 PUT')
    args = parser.parse_args(argv)
    try:
        uuid, recipe, sha = validate_copy(args.backup, args.confirm_private_copy)
        candidate = recipe.copy()  # unchanged GET payload; no invented catalog names
        if args.mode == 'prepare':
            from .myspeidel_put_experiments import offline_check
            result = {
                'format': FORMAT, 'mode': 'prepare', 'source_url': SOURCE_URL,
                'baseline_sha256': sha, 'candidate_sha256': digest(candidate),
                'unchanged_payload': True, 'source_is_user_attested_copy': True,
                'supported_schema_checks': offline_check(args.spec, candidate) if args.spec else None,
                'network_requests': 0, 'upload_ready': False,
            }
            write_new(private_file(args.result), result)
            print('OFFLINE golden-copy report saved; no API access.')
            return 0
        if args.spec:
            raise ValueError('--spec is supported only for prepare')
        if args.mode == 'apply' and not args.allow_live_write:
            raise ValueError('Real PUT requires --allow-live-write')
        # Reuse the established durable preflight, explicit input confirmation,
        # server-digest check, diagnostic receipt, and GET-after-PUT verification.
        from .myspeidel_put_experiments import _run_online
        args.variant = 'original'
        _run_online(args, uuid, recipe, sha, candidate, digest(candidate))
        return 0
    except Exception as exc:
        # Avoid printing arbitrary server or recipe content.
        print('Golden roundtrip stopped: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
