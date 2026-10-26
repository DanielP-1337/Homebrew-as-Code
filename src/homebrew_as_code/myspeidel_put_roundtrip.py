"""Narrow PUT transport and integrity checks for explicitly selected private recipes.

The existing MySpeidelClient is deliberately GET-only; this is an isolated opt-in
writer for PUT /v1.0/recipe/{uuid}, not an extension of its general allowlist.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .myspeidel import BASE_URL, UUID_PATTERN, MySpeidelError

MAX_BYTES = 5_000_000
MAX_RESPONSE_BYTES = 65_536


class PutDiagnosticError(MySpeidelError):
    """Safe, bounded PUT diagnostic; never hold or reveal server response text."""

    def __init__(self, status: int | None, category: str = 'unclassified',
                 location: str = 'unknown', paths: tuple[str, ...] = ()) -> None:
        self.status = status
        self.category = category
        self.location = location
        self.paths = paths
        self.validation_details = None
        super().__init__('PUT diagnostic available; private response suppressed')


# Classification is deliberately coarse. Never print server-supplied strings.
def classify_put_error(data: bytes) -> tuple[str, str]:
    try:
        obj = json.loads(data)
    except (ValueError, UnicodeError, TypeError):
        return 'unclassified', 'unknown'
    if not isinstance(obj, dict):
        return 'unclassified', 'unknown'
    errors = obj.get('errors')
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            path = first.get('path')
            location = 'unknown'
            if isinstance(path, str):
                # Only known schema root names; never print arbitrary paths/values.
                for root in ('uuid', 'public', 'recipe_type', 'water_plato',
                             'machine_type', 'owner', 'brewer', 'mashing', 'rest',
                             'boil', 'fermentation', 'maturation', 'references'):
                    if path in (root, '$.' + root) or path.startswith('$.' + root + '.') or path.startswith('$.' + root + '['):
                        location = root
                        break
            return 'schema_validation', location
    if 'error' in obj:
        return 'server_rejection', 'unknown'
    return 'unclassified', 'unknown'


# Allow only fixed, non-identifying field names and array indexes from errors[].path.
# Never echo a server-supplied string verbatim: a path might contain a private UUID.
_SAFE_SEGMENTS = frozenset({
    'uuid', 'parent_uuid', 'owner_uuid', 'public', 'recipe_type', 'water_plato', 'name',
    'schema_version', 'content_version', 'owner', 'brewer', 'machine_type',
    'size', 'mashing', 'rest', 'boil', 'fermentation', 'maturation',
    'references', 'adds', 'water', 'malts', 'malt_uuid', 'hops', 'hop_uuid',
    'ingredients', 'ingredient_uuid', 'yeasts', 'yeast_uuid', 'steps',
    'temperature', 'duration', 'amount', 'color', 'acid', 'sorting',
    'boiling_duration', 'boiling_temperature', 'phases', 'created_on',
    'update_on', 'creation_date', 'water_amount_start', 'water_amount_addition',
    'bitterness', 'style', 'description', 'comments', 'country',
    'water_recast', 'water_specific_gravity', 'brewing_set_active',
})


def safe_schema_path(value: Any) -> str | None:
    """Normalize ONLY allowlisted paths; private map keys/identifiers are never exposed."""
    import re
    if not isinstance(value, str) or len(value) > 512:
        return None
    path = value.strip()
    if path.startswith('body.'):
        path = path[5:]
    if path.startswith('#/'):
        path = path[2:].replace('/', '.')
    elif path.startswith('/'):
        path = path[1:].replace('/', '.')
    if path.startswith('$.'):
        path = path[2:]
    elif path == '$':
        return '$'
    pieces = re.findall(r'([A-Za-z_][A-Za-z_0-9]*)(\[\d+\])*', path)
    if not pieces:
        return None
    rebuilt = '.'.join(name + idx for name, idx in pieces)
    if rebuilt != path or any(name not in _SAFE_SEGMENTS for name, _ in pieces):
        return None
    return '$.' + rebuilt


def safe_validation_paths(data: bytes, limit: int = 8) -> tuple[str, ...]:
    """Extract validated JSON field paths; never retain server descriptions."""
    try:
        value = json.loads(data)
    except (UnicodeError, ValueError, TypeError):
        return ()
    if not isinstance(value, dict) or not isinstance(value.get('errors'), list):
        return ()
    result = []
    for error in value['errors'][:64]:
        if not isinstance(error, dict):
            continue
        path = safe_schema_path(error.get('path'))
        if path and path not in result:
            result.append(path)
        if len(result) == limit:
            break
    return tuple(result)


def dry_run_acknowledged(response: bytes) -> bool:
    """Accept only the documented exact acknowledgement, not arbitrary HTTP 200."""
    try:
        decoded = response.decode('utf-8').strip()
    except UnicodeError:
        return False
    if decoded == 'DRY RUN SUCCEEDED':
        return True
    try:
        parsed = json.loads(decoded)
    except (ValueError, TypeError):
        return False
    return (isinstance(parsed, dict) and
            parsed.get('message') == 'DRY RUN SUCCEEDED')


def serialized(recipe: dict[str, Any]) -> bytes:
    return json.dumps(recipe, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(recipe: dict[str, Any]) -> str:
    return hashlib.sha256(serialized(recipe)).hexdigest()


def check_private(recipe: Any, uuid: str) -> dict[str, Any]:
    if not isinstance(uuid, str) or UUID_PATTERN.fullmatch(uuid) is None:
        raise ValueError('Invalid recipe UUID')
    if not isinstance(recipe, dict) or recipe.get('uuid') != uuid:
        raise ValueError('Recipe identity mismatch')
    if type(recipe.get('public')) is not int or recipe['public'] != 0:
        raise ValueError('Recipe is not explicitly private')
    machine = recipe.get('machine_type')
    if not isinstance(machine, dict) or type(machine.get('size')) is not int or machine['size'] != 20:
        raise ValueError('Expected a private 20 L test recipe')
    return recipe


def private_file(path: str, *, must_exist: bool = False) -> Path:
    p = Path(path).resolve()
    root = (Path.cwd() / '.local').resolve()
    if root not in p.parents:
        raise ValueError('Files must be located under project .local')
    if must_exist and not p.is_file():
        raise ValueError('Private input file missing')
    if not must_exist and p.exists():
        raise ValueError('Refusing to overwrite existing private file')
    return p


def write_new(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    # Exclusive creation prevents overwriting prior evidence.
    with path.open('xb') as stream:
        stream.write(raw)


def read_backup(path: Path) -> tuple[str, dict[str, Any], str]:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Backup exceeds size limit')
    item = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(item, dict) or item.get('format') != 'homebrew-as-code/myspeidel-put-backup-v1':
        raise ValueError('Unexpected backup format')
    uuid, recipe, sha = item.get('uuid'), item.get('recipe'), item.get('sha256')
    check_private(recipe, uuid)
    if not isinstance(sha, str) or digest(recipe) != sha:
        raise ValueError('Backup digest mismatch')
    return uuid, recipe, sha


def put_recipe(token: str, uuid: str, recipe: dict[str, Any], *, dry_run: bool,
               opener: Callable[..., Any] | None = None,
               diagnostic_events: list[dict] | None = None) -> int:
    check_private(recipe, uuid)
    if not isinstance(token, str) or not token or '\r' in token or '\n' in token:
        raise ValueError('Invalid token')
    if type(dry_run) is not bool:
        raise ValueError('dry_run must be bool')
    if diagnostic_events is not None and not dry_run:
        raise ValueError('Development diagnostics require dry_run=True')
    from .myspeidel_dev_diagnostics import request_event, response_event
    url = BASE_URL + '/v1.0/recipe/' + uuid + ('?dryRun=1' if dry_run else '')
    payload = serialized(recipe)
    if len(payload) > MAX_BYTES:
        raise ValueError('Recipe exceeds request size limit')
    req = urllib.request.Request(url, data=payload, method='PUT', headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/json',
        'Content-Type': 'application/json', 'User-Agent': 'Homebrew-as-Code/0.2.0'})
    if diagnostic_events is not None:
        diagnostic_events.append(request_event(req, token))
    try:
        with (opener or urllib.request.urlopen)(req, timeout=20) as res:
            status = res.status
            response = res.read(MAX_RESPONSE_BYTES + 1)
            if diagnostic_events is not None:
                diagnostic_events.append(response_event(status, getattr(res, "headers", None), response, token, MAX_RESPONSE_BYTES))
            if status != 200:
                raise PutDiagnosticError(status)
            if dry_run and (len(response) > MAX_RESPONSE_BYTES or
                            not dry_run_acknowledged(response)):
                raise PutDiagnosticError(200, 'dry_run_ack_unverified')
            return status
    except urllib.error.HTTPError as exc:
        try:
            response = exc.read(MAX_RESPONSE_BYTES + 1)
        except (OSError, ValueError):
            response = b''
        if diagnostic_events is not None:
            diagnostic_events.append(response_event(exc.code, exc.headers, response, token, MAX_RESPONSE_BYTES))
        category, location = classify_put_error(response[:MAX_RESPONSE_BYTES])
        paths = safe_validation_paths(response[:MAX_RESPONSE_BYTES])
        diagnostic = PutDiagnosticError(exc.code, category, location, paths)
        if exc.code == 400:
            from .myspeidel_server_validation import summarize_server_validation
            diagnostic.validation_details = summarize_server_validation(response)
        # Developer opt-in: keep raw HTTP error strictly outside publishable receipts.
        import os
        if os.environ.get('HBAC_MYSPEIDEL_LOCAL_HTTP_ERROR') == '1':
            content_type = exc.headers.get('Content-Type', '') if exc.headers else ''
            # Do not copy arbitrary response headers; content-type is allowlisted.
            if not isinstance(content_type, str) or len(content_type) > 160:
                content_type = 'unavailable'
            diagnostic.local_http_error = {
                'http_status': exc.code,
                'content_type': content_type,
                'body_text': response[:MAX_RESPONSE_BYTES].decode('utf-8', errors='replace'),
                'body_truncated': len(response) > MAX_RESPONSE_BYTES,
                'body_bytes_captured': min(len(response), MAX_RESPONSE_BYTES),
            }
        raise diagnostic from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise PutDiagnosticError(None, 'transport_uncertain') from None
