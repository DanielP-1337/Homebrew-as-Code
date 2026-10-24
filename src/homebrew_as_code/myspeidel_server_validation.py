"""Bounded, value-free summary of MySpeidel PUT error responses.

Never persist messages, response bodies, arbitrary field names or identifiers.
This summary is diagnostic evidence, not a validation guarantee.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Explicit, auditable static schema-property allowlist. Unknown tokens are masked.
STATIC = frozenset({
    'uuid', 'name', 'public', 'recipe_type', 'water_plato', 'references',
    'owner', 'brewer', 'machine_type', 'size', 'mashing', 'rest', 'boil',
    'fermentation', 'maturation', 'water_types', 'malts', 'hops',
    'ingredients', 'yeasts', 'steps', 'adds', 'water', 'malt_uuid',
    'hop_uuid', 'ingredient_uuid', 'yeast_uuid', 'owner_uuid',
    'parent_uuid', 'temperature', 'duration', 'amount', 'color',
    'schema_version', 'content_version', 'sorting',
})
ERROR_CODES = frozenset({
    'openapivalidation', 'required', 'type', 'enum', 'format',
    'minimum', 'maximum', 'minlength', 'maxlength', 'pattern',
    'additionalproperties', 'oneof', 'anyof', 'allof',
})
MAX_ERRORS = 32
MAX_PATHS = 8
MAX_RESPONSE = 65_536

# Output only these literal field names. Never serialize arbitrary keys or values.
SHAPE_FIELDS = frozenset({
    'path', 'message', 'errorCode', 'code', 'keyword', 'instancePath',
    'dataPath', 'params', 'details', 'field', 'location', 'errors',
})
SHAPE_TYPES = frozenset({'null', 'boolean', 'number', 'string', 'array', 'object'})
MAX_SHAPES = 12


def _value_type(value: Any) -> str:
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, (int, float)):
        return 'number'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, list):
        return 'array'
    return 'object'


def _shape(error: Any) -> dict[str, Any]:
    """Return only allowlisted keys and coarse types, never server values."""
    if not isinstance(error, dict):
        return {'kind': _value_type(error)}
    fields = {key: _value_type(error[key]) for key in sorted(SHAPE_FIELDS)
              if key in error}
    return {
        'kind': 'object', 'fields': fields,
        'other_key_count': min(sum(key not in SHAPE_FIELDS for key in error), 32),
    }


def _safe_path(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 1024:
        return 'unknown'
    if not value.startswith('$.'):
        return 'unknown'
    # Reject noncanonical expressions instead of trying to interpret them.
    if not re.fullmatch(r'\$\.[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+|\[\d+\])*', value):
        return 'unknown'
    tokens = re.findall(r'[A-Za-z0-9_-]+|\[\d+\]', value[2:])
    if len(tokens) > 24:
        return 'unknown'
    # Do not reveal unknown root names. Mask intermediate dynamic map keys.
    if not tokens or tokens[0] not in STATIC:
        return 'unknown'
    return '$.' + '.'.join('[*]' if token.startswith('[') else
                          token if token in STATIC else '<redacted>'
                          for token in tokens).replace('.[*]', '[*]')


def summarize_server_validation(response: bytes) -> dict[str, Any]:
    """Parse a bounded error body into a fixed-schema, safe dictionary."""
    result: dict[str, Any] = {
        'response_format': 'unknown', 'error_count': 0,
        'error_count_truncated': False, 'safe_paths': [],
        'known_error_codes': [], 'pathless_errors': 0,
        'error_shapes': [],
    }
    if not isinstance(response, bytes) or len(response) > MAX_RESPONSE:
        result['response_format'] = 'oversized_or_unavailable'
        return result
    try:
        value = json.loads(response)
    except (ValueError, UnicodeError, TypeError):
        return result
    if not isinstance(value, dict):
        result['response_format'] = 'json_other'
        return result
    result['response_format'] = 'json_object'
    errors = value.get('errors')
    if not isinstance(errors, list):
        result['response_format'] = 'json_without_errors_array'
        return result
    result['error_count'] = min(len(errors), MAX_ERRORS)
    result['error_count_truncated'] = len(errors) > MAX_ERRORS
    shape_counts: dict[str, int] = {}
    paths: set[str] = set()
    codes: set[str] = set()
    for error in errors[:MAX_ERRORS]:
        # Canonical serialization is generated solely from fixed field names/types.
        signature = json.dumps(_shape(error), sort_keys=True)
        shape_counts[signature] = shape_counts.get(signature, 0) + 1
        if not isinstance(error, dict):
            result['pathless_errors'] += 1
            continue
        path = _safe_path(error.get('path'))
        if path == 'unknown':
            result['pathless_errors'] += 1
        else:
            paths.add(path)
        code = error.get('errorCode')
        if isinstance(code, str) and code.lower() in ERROR_CODES:
            codes.add(code.lower())
    result['error_shapes'] = [
        {'count': count, **json.loads(signature)}
        for signature, count in sorted(shape_counts.items())[:MAX_SHAPES]
    ]
    result['safe_paths'] = sorted(paths)[:MAX_PATHS]
    result['known_error_codes'] = sorted(codes)
    return result
