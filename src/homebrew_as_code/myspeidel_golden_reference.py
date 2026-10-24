"""Offline MySpeidel golden-reference inspection. Never transmits recipes.

The vendor's example belongs to the vendor; do not commit a copied specimen.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _ref(spec: dict, value: Any) -> Any:
    seen: set[str] = set()
    while isinstance(value, dict) and '$ref' in value:
        path = value['$ref']
        if not isinstance(path, str) or not path.startswith('#/') or path in seen:
            raise ValueError('Unsupported or cyclic OpenAPI reference')
        seen.add(path)
        current: Any = spec
        for segment in path[2:].split('/'):
            key = segment.replace('~1', '/').replace('~0', '~')
            if not isinstance(current, dict) or key not in current:
                raise ValueError('Invalid OpenAPI reference')
            current = current[key]
        value = current
    return value


def _schema_ref(spec: dict, method: str, path: str) -> dict:
    op = spec['paths'][path][method]
    if method == 'post':
        media = op['requestBody']['content']['application/json']
    else:
        media = op['responses']['200']['content']['application/json']
    schema = media['schema']
    return _ref(spec, schema)


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(child) for key, child in sorted(value.items())}
    if isinstance(value, list):
        return {'type': 'array', 'length': len(value), 'items': _shape(value[0]) if value else None}
    return 'null' if value is None else ('boolean' if isinstance(value, bool) else 'number' if isinstance(value, (int, float)) else 'string' if isinstance(value, str) else 'unknown')


def inspect(spec_bytes: bytes) -> dict[str, Any]:
    spec = json.loads(spec_bytes)
    if not isinstance(spec, dict) or not str(spec.get('openapi', '')).startswith('3.0.'):
        raise ValueError('Requires OpenAPI 3.0.x specification')
    example = _ref(spec, spec['components']['examples']['recipe'])
    if not isinstance(example, dict) or not isinstance(example.get('value'), dict):
        raise ValueError('Missing manufacturer example')
    recipe = example['value']
    schema = _ref(spec, spec['components']['schemas']['recipe_v5'])
    required = schema.get('required', [])
    if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
        raise ValueError('Invalid required fields')
    post_op = spec['paths']['/v1.0/recipe']['post']
    params = [_ref(spec, p) for p in post_op.get('parameters', [])]
    dryrun = [p for p in params if p.get('name') == 'dryRun']
    post_schema = post_op['requestBody']['content']['application/json']['schema']
    post_refs = [v['$ref'] for v in post_schema.get('oneOf', []) if isinstance(v, dict) and '$ref' in v]
    if '$ref' in post_schema:
        post_refs.append(post_schema['$ref'])
    get_schema = spec['paths']['/v1.0/recipe/{uuid}']['get']['responses']['200']['content']['application/json']['schema']
    return {
        'format': 'homebrew-as-code/myspeidel-golden-reference-v1',
        'offline': True, 'upload_ready': False, 'api_payload': None,
        'spec_sha256': hashlib.sha256(spec_bytes).hexdigest(),
        'openapi_version': spec['openapi'],
        'post_schema_refs': post_refs,
        'get_schema_ref': get_schema.get('$ref'),
        'dryrun_documented': bool(dryrun),
        'dryrun_metadata': [{'name': p.get('name'), 'in': p.get('in'), 'required': p.get('required', False), 'schema': _shape(p.get('schema', {}))} for p in dryrun],
        'top_level_required_count': len(required),
        'example_present_required_count': sum(x in recipe for x in required),
        'example_missing_required': sorted(set(required) - set(recipe)),
        'example_extra_top_level': sorted(set(recipe) - set(schema.get('properties', {}))),
        'example_structure': _shape(recipe),
        'never_upload_example_unchanged': True,
        'blockers': [
            'Manufacturer example may contain foreign UUIDs, owner references and timestamps',
            'Missing schema-required example fields must be resolved without inventing values',
            'OpenAPI structure inventory is not complete schema or semantic validation',
            'Dry-run side effects have not been independently confirmed',
            'No authentication, POST, PUT or DELETE is implemented in this tool',
        ],
    }


def inspect_file(path: str | Path) -> dict[str, Any]:
    return inspect(Path(path).read_bytes())
