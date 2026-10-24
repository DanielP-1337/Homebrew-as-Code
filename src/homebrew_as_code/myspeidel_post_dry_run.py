"""Experimental MySpeidel recipe creation dry-run; no live-create capability.

Reads a digest-checked private backup. Never sends to /v1.0/recipe without
?dryRun=1. HTTP responses and tokens are never copied to diagnostics.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid as uuidlib

from .myspeidel_put_roundtrip import private_file, read_backup

MAX_BYTES = 5_000_000


def dry_run_acknowledged(data):
    try:
        content = data.decode("utf-8").strip()
        if content == "DRY RUN SUCCEEDED":
            return True
        obj = json.loads(content)
        return isinstance(obj, dict) and obj.get("message") == "DRY RUN SUCCEEDED"
    except (UnicodeError, ValueError, TypeError):
        return False


def safe_validation_paths(data):
    """Never expose UUIDs, ingredient names or server-authored error text."""
    import re
    allowed = {"uuid", "public", "recipe_type", "machine_type", "size",
               "references", "name", "water_plato", "mashing", "boil",
               "fermentation", "maturation", "malts", "hops", "yeasts",
               "water_types", "ingredients", "owner", "brewer", "steps",
               "adds", "amount", "acid", "color", "duration"}
    try:
        obj = json.loads(data)
    except (UnicodeError, ValueError, TypeError):
        return ()
    if not isinstance(obj, dict) or not isinstance(obj.get("errors"), list):
        return ()
    found = []
    for error in obj["errors"][:32]:
        value = error.get("path") if isinstance(error, dict) else None
        if not isinstance(value, str) or len(value) > 256:
            continue
        path = value[2:] if value.startswith("$.") else value
        parts = path.split(".")
        if parts and all(re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", p) and p in allowed for p in parts):
            found.append("$." + ".".join(parts))
    return tuple(dict.fromkeys(found[:8]))


def classify_put_error(data):
    paths = safe_validation_paths(data)
    if paths:
        return "schema_validation", paths[0].split(".")[1]
    return "unclassified", "unknown"

DRY_RUN_URL = 'https://api.cloud.myspeidel.com/v1.0/recipe?dryRun=1'
FORMAT = 'homebrew-as-code/myspeidel-post-dry-run-v1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def prepare(recipe, *, title, new_uuid):
    """Create independent candidate preserving references as unverified evidence.

    This is not an ingredient identity remapper. A rejected dry run is expected
    until the server's create contract is understood.
    """
    if not isinstance(recipe, dict) or not isinstance(title, str) or not title.strip():
        raise ValueError('Invalid source recipe or title')
    if title == recipe.get('name') or len(title) > 200:
        raise ValueError('Candidate must have a distinct, bounded name')
    parsed = uuidlib.UUID(new_uuid)
    if str(parsed) != new_uuid or new_uuid == recipe.get('uuid'):
        raise ValueError('New UUID must be distinct and canonical')
    candidate = copy.deepcopy(recipe)
    candidate['uuid'] = new_uuid
    candidate['name'] = title.strip()
    candidate['public'] = 0
    # The owner / ingredient catalog data in an existing recipe are not
    # transferable identities. Preserve them for diagnostic schema checks,
    # but explicitly flag possible cross-recipe shared-reference rejection.
    return candidate


def inspect(candidate):
    if not isinstance(candidate, dict) or candidate.get('public') != 0:
        raise ValueError('Only explicitly private candidates are supported')
    if not isinstance(candidate.get('references'), dict):
        raise ValueError('References catalog is missing')
    if not isinstance(candidate.get('machine_type'), dict) or candidate['machine_type'].get('size') != 20:
        raise ValueError('Only Braumeister 20 L candidates are supported')
    for group in ('malts', 'hops', 'water_types', 'yeasts', 'ingredients'):
        if group in candidate['references'] and not isinstance(candidate['references'][group], dict):
            raise ValueError('Malformed reference catalog')
    payload = canonical(candidate)
    if len(payload) > MAX_BYTES:
        raise ValueError('Candidate exceeds size limit')
    return {
        'format': FORMAT,
        'status': 'OFFLINE_PREPARED',
        'candidate_sha256': hashlib.sha256(payload).hexdigest(),
        'candidate_uuid': candidate['uuid'],
        'candidate_name': candidate['name'],
        'private': True,
        'machine_size_l': 20,
        'reference_counts': {group: len(refs) for group, refs in candidate['references'].items()
                             if isinstance(refs, dict)},
        'warnings': [
            'This is a copied recipe candidate, not a validated create schema.',
            'Existing source ingredient UUIDs and owner metadata are retained only as a test; server may reject shared references.',
            'No ingredient identities have been verified or merged.',
            'A successful POST dry-run is not proof that a live create is safe.',
            'This tool cannot make a live create request.',
        ],
    }


def _read_candidate(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Candidate file exceeds size limit')
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or raw.get('format') != FORMAT:
        raise ValueError('Unexpected candidate file format')
    recipe, expected = raw.get('recipe'), raw.get('sha256')
    if not isinstance(recipe, dict) or not isinstance(expected, str):
        raise ValueError('Malformed candidate file')
    report = inspect(recipe)
    if report['candidate_sha256'] != expected:
        raise ValueError('Candidate digest mismatch')
    return recipe, report


def send_dry_run(token, candidate, *, opener=None):
    """One bounded dryRun=1 POST. NEVER retry and NEVER call a live endpoint."""
    if not isinstance(token, str) or not token or '\r' in token or '\n' in token:
        raise ValueError('Invalid token')
    report = inspect(candidate)
    body = canonical(candidate)
    req = urllib.request.Request(DRY_RUN_URL, data=body, method='POST', headers={
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Homebrew-as-Code/0.2.0',
    })
    # Only this literal URL is permitted: do not allow external url arguments.
    if req.full_url != DRY_RUN_URL or req.get_method() != 'POST':
        raise RuntimeError('Dry-run safety invariant failed')
    try:
        with (opener or urllib.request.urlopen)(req, timeout=20) as response:
            status = response.status
            response_body = response.read(65_537)
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_body = exc.read(65_537)
    except (urllib.error.URLError, OSError, TimeoutError):
        return {'status': 'TRANSPORT_UNCERTAIN', 'http_status': None,
                'candidate_sha256': report['candidate_sha256'],
                'acknowledged': False, 'error_paths': []}
    response_body = response_body[:65_536]
    # The documented dry-run response is exactly DRY RUN SUCCEEDED, either
    # text or JSON message; non-matching HTTP 200 is explicitly unverified.
    acknowledged = status == 200 and dry_run_acknowledged(response_body)
    category, location = classify_put_error(response_body)
    return {'status': 'DRY_RUN_ACKNOWLEDGED' if acknowledged else 'UNVERIFIED_RESPONSE',
            'http_status': status, 'candidate_sha256': report['candidate_sha256'],
            'acknowledged': acknowledged, 'error_category': category,
            'error_location': location,
            'error_paths': list(safe_validation_paths(response_body))}


def main(argv=None):
    parser = argparse.ArgumentParser(description='MySpeidel POST dry-run only; never creates recipes')
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--backup', required=True)
    prep.add_argument('--candidate', required=True)
    prep.add_argument('--report', required=True)
    prep.add_argument('--name', required=True)
    check = sub.add_parser('dry-run')
    check.add_argument('--candidate', required=True)
    check.add_argument('--report', required=True)
    check.add_argument('--confirm-sha256', required=True,
                       help='Full 64-char candidate SHA-256, reviewed offline')
    check.add_argument('--token-env', default='MYSPEIDEL_TOKEN')
    args = parser.parse_args(argv)
    try:
        candidate_path = private_file(args.candidate, must_exist=args.action == 'dry-run')
        report_path = private_file(args.report)
        if args.action == 'prepare':
            backup_path = private_file(args.backup, must_exist=True)
            _, recipe, source_sha = read_backup(backup_path)
            candidate = prepare(recipe, title=args.name, new_uuid=str(uuidlib.uuid4()))
            report = inspect(candidate)
            report['source_sha256'] = source_sha
            candidate_path.parent.mkdir(parents=True, exist_ok=True)
            with candidate_path.open('x', encoding='utf-8') as stream:
                json.dump({'format': FORMAT, 'sha256': sha256(candidate), 'recipe': candidate},
                          stream, ensure_ascii=False, indent=2)
        else:
            candidate, _ = _read_candidate(candidate_path)
            expected = sha256(candidate)
            if args.confirm_sha256 != expected:
                raise ValueError('Explicit SHA-256 confirmation mismatch')
            token = os.environ.get(args.token_env, '')
            if not token:
                raise ValueError('Token environment variable unavailable')
            report = send_dry_run(token, candidate)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        print('Offline candidate prepared; no HTTP.' if args.action == 'prepare' else
              f'POST dryRun=1 result: {report["status"]}; HTTP {report["http_status"]}.')
        return 0 if args.action == 'prepare' or report['acknowledged'] else 2
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        # Do not print exception text: a request failure may contain private values.
        print(f'POST dry-run stopped: {type(exc).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
