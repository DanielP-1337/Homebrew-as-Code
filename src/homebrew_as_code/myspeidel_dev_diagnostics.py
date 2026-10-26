"""Development-only dry-run evidence. Recipe values visible; credentials masked."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

MASK = '[REDACTED]'
_SECRET = re.compile(r'authorization|cookie|password|passwd|secret|token|api[-_]?key', re.I)


def redact(value: Any, token: str) -> Any:
    """Mask credential fields, known bearer token and common text credential forms."""
    if isinstance(value, dict):
        return {redact(str(k), token): MASK if _SECRET.search(str(k)) else redact(v, token)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, token) for v in value]
    if not isinstance(value, str):
        return value
    if token:
        value = value.replace(token, MASK)
        value = value.replace(json.dumps(token)[1:-1], MASK)
    value = re.sub(r'(?i)\b(Bearer|Basic)\s+[^\s"<>;,]+', r'\1 [REDACTED]', value)
    value = re.sub(r'(?i)((?:password|passwd|access_token|refresh_token|token|client_secret|api_key)\s*[=:]\s*)("[^"]*"|\x27[^\x27]*\x27|[^\s&,;<>]+)',
                   r'\1[REDACTED]', value)
    value = re.sub(r'(?im)^((?:proxy-)?authorization|(?:set-)?cookie)\s*:.*$',
                   r'\1: [REDACTED]', value)
    return value


def body_view(data: bytes, token: str) -> dict:
    text = data.decode('utf-8', errors='replace')
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError):
        return {'body_text': redact(text, token), 'body_format': 'text'}
    return {'body': redact(parsed, token), 'body_format': 'json'}


def request_event(request, token: str) -> dict:
    payload = request.data
    parsed = json.loads(payload)
    return {
        'event': 'request_prepared', 'method': request.get_method(),
        'url': redact(request.full_url, token),
        'headers': redact(dict(request.header_items()), token),
        'headers_scope': 'urllib Request headers before transport; transport may add Host/Content-Length',
        'body_bytes': len(payload), 'body_sha256': hashlib.sha256(payload).hexdigest(),
        'body_text': json.dumps(redact(parsed, token), ensure_ascii=False, sort_keys=True, separators=(',', ':')),
        'root_keys': sorted(parsed),
        'backup_wrapper_detected': 'recipe' in parsed and 'format' in parsed,
        'body_scope': 'Exact serialized request text except credential redaction; digest uses sent bytes',
    }


def response_event(status, headers, data: bytes, token: str, limit: int) -> dict:
    captured = data[:limit]
    return {
        'event': 'response', 'http_status': status,
        'headers': redact(dict(headers.items()) if headers is not None else {}, token),
        'body_bytes_captured': len(captured), 'body_truncated': len(data) > limit,
        **body_view(captured, token),
    }
