"""Offline OpenAPI 3.0 recipe_v5 reference candidate validation.

No network, authentication, recipe upload, or private values in reports.
This is a conservative supported-keyword validator, NOT a full OAS validator.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .myspeidel_golden_reference import _ref

OBSERVED_FIELDS = {'public': 0, 'recipe_type': 0, 'water_plato': 12}
SUPPORTED = {'$ref', 'type', 'nullable', 'required', 'properties', 'items',
             'additionalProperties', 'allOf', 'anyOf', 'oneOf', 'not', 'enum',
             'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
             'minLength', 'maxLength', 'pattern', 'minItems', 'maxItems',
             'uniqueItems', 'minProperties', 'maxProperties', 'multipleOf',
             'format', 'description', 'title', 'example', 'default', 'deprecated',
             'readOnly', 'writeOnly', 'discriminator', 'xml', 'externalDocs'}
ANNOTATIONS = {'description', 'title', 'example', 'default', 'deprecated',
               'xml', 'externalDocs', 'discriminator'}


def _issues(spec: dict, schema: Any, value: Any, path: str, depth: int = 0) -> tuple[list[dict], list[dict]]:
    errors: list[dict] = []
    unsupported: list[dict] = []

    def error(code: str, at: str = path) -> None:
        errors.append({'path': at, 'code': code})

    def blocked(code: str, at: str = path) -> None:
        unsupported.append({'path': at, 'code': code})

    if depth > 64:
        blocked('schema_depth_limit')
        return errors, unsupported
    if not isinstance(schema, dict):
        blocked('schema_not_object')
        return errors, unsupported
    for keyword in schema:
        if keyword not in SUPPORTED and not keyword.startswith('x-'):
            blocked('unknown_keyword:' + keyword)
    if '$ref' in schema:
        # OpenAPI 3 Reference Objects cannot redefine the referenced schema.
        if any(k != '$ref' for k in schema):
            blocked('reference_siblings_ignored')
        try:
            resolved = _ref(spec, {'$ref': schema['$ref']})
        except (ValueError, KeyError, TypeError):
            blocked('unresolved_reference')
            return errors, unsupported
        return _issues(spec, resolved, value, path, depth + 1)
    if schema.get('nullable') is True and value is None:
        # OAS 3.0 nullable applies if type is explicitly defined.
        if 'type' in schema:
            return errors, unsupported
    if 'enum' in schema and value not in schema['enum']:
        error('enum_mismatch')
    typ = schema.get('type')
    match = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str),
             'integer': isinstance(value, int) and not isinstance(value, bool),
             'number': isinstance(value, (int, float)) and not isinstance(value, bool),
             'boolean': isinstance(value, bool)}
    if typ is not None:
        if typ not in match:
            blocked('unknown_type')
        elif not match[typ]:
            error('type_mismatch')
            return errors, unsupported
    if isinstance(value, dict):
        req = schema.get('required', [])
        if not isinstance(req, list):
            blocked('invalid_required_definition')
        else:
            for key in req:
                if key not in value:
                    error('required_missing', path + '.' + str(key))
        for limit, fn in (('minProperties', lambda a, b: a < b), ('maxProperties', lambda a, b: a > b)):
            if limit in schema and fn(len(value), schema[limit]):
                error(limit)
        properties = schema.get('properties', {})
        if not isinstance(properties, dict):
            blocked('invalid_properties_definition')
            properties = {}
        for key, child in value.items():
            childpath = path + '.' + str(key)
            if key in properties:
                ce, cu = _issues(spec, properties[key], child, childpath, depth + 1)
                errors.extend(ce); unsupported.extend(cu)
            elif schema.get('additionalProperties') is False:
                error('additional_property', childpath)
            elif isinstance(schema.get('additionalProperties'), dict):
                ce, cu = _issues(spec, schema['additionalProperties'], child, childpath, depth + 1)
                errors.extend(ce); unsupported.extend(cu)
    if isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            error('minItems')
        if 'maxItems' in schema and len(value) > schema['maxItems']:
            error('maxItems')
        if schema.get('uniqueItems') is True:
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            if len(set(encoded)) != len(encoded):
                error('uniqueItems')
        if 'items' in schema:
            for n, item in enumerate(value):
                ce, cu = _issues(spec, schema['items'], item, f'{path}[{n}]', depth + 1)
                errors.extend(ce); unsupported.extend(cu)
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            error('minLength')
        if 'maxLength' in schema and len(value) > schema['maxLength']:
            error('maxLength')
        if 'pattern' in schema:
            try:
                if re.search(schema['pattern'], value) is None:
                    error('pattern')
            except re.error:
                blocked('invalid_pattern')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        for key in ('minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum'):
            if key not in schema:
                continue
            bound = schema[key]
            if key == 'minimum' and value < bound: error(key)
            if key == 'maximum' and value > bound: error(key)
            if key == 'exclusiveMinimum':
                if isinstance(bound, bool):
                    if bound and 'minimum' in schema and value <= schema['minimum']: error(key)
                else:
                    blocked('exclusiveMinimum_non_boolean_oas3')
            if key == 'exclusiveMaximum':
                if isinstance(bound, bool):
                    if bound and 'maximum' in schema and value >= schema['maximum']: error(key)
                else:
                    blocked('exclusiveMaximum_non_boolean_oas3')
        if 'multipleOf' in schema:
            multiple = schema['multipleOf']
            if not isinstance(multiple, (int, float)) or multiple <= 0:
                blocked('invalid_multipleOf')
            elif abs(value / multiple - round(value / multiple)) > 1e-8:
                error('multipleOf')
    if schema.get('readOnly') or schema.get('writeOnly'):
        blocked('directional_property_context_not_validated')
    if schema.get('format') and schema['format'] not in ('double', 'float', 'int32', 'int64'):
        blocked('format_not_validated:' + str(schema['format']))
    for keyword in ('allOf', 'anyOf', 'oneOf'):
        if keyword not in schema:
            continue
        alternatives = schema[keyword]
        if not isinstance(alternatives, list):
            blocked('invalid_' + keyword)
            continue
        results = [_issues(spec, alt, value, path, depth + 1) for alt in alternatives]
        good = [not e and not u for e, u in results]
        if keyword == 'allOf':
            for e, u in results:
                errors.extend(e); unsupported.extend(u)
        elif any(u for _, u in results):
            blocked(keyword + '_has_unverified_branches')
        elif (keyword == 'oneOf' and sum(good) != 1) or (keyword == 'anyOf' and not any(good)):
            error(keyword + '_mismatch')
    if 'not' in schema:
        e, u = _issues(spec, schema['not'], value, path, depth + 1)
        if u: blocked('not_unverified')
        elif not e: error('not_mismatch')
    return errors, unsupported


def build_report(spec_bytes: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = json.loads(spec_bytes)
    if not isinstance(spec, dict) or not str(spec.get('openapi', '')).startswith('3.0.'):
        raise ValueError('Requires OpenAPI 3.0.x document')
    example = _ref(spec, spec['components']['examples']['recipe'])['value']
    if not isinstance(example, dict):
        raise ValueError('Reference recipe example is not an object')
    candidate = copy.deepcopy(example)
    if any(field in candidate for field in OBSERVED_FIELDS):
        raise ValueError('Reference unexpectedly already defines a field to supplement')
    candidate.update(OBSERVED_FIELDS)
    schema = spec['components']['schemas']['recipe_v5']
    errors, unsupported = _issues(spec, schema, candidate, '$')
    report = {
        'format': 'homebrew-as-code/myspeidel-golden-validation-v1',
        'offline': True, 'upload_ready': False, 'api_payload': None,
        'spec_sha256': hashlib.sha256(spec_bytes).hexdigest(),
        'supplemented_fields': sorted(OBSERVED_FIELDS),
        'supplement_source': 'Observed GET values of one private recipe; NOT universal POST defaults',
        'validation_scope': 'Conservative OpenAPI 3.0 supported-keyword recursive check; not full standards validation',
        'schema_errors': errors, 'unverified_constraints': unsupported,
        'schema_check_passed': not errors and not unsupported,
        'blockers': ['Owner, UUID, parent, timestamps and ingredient references NOT sanitized',
                     'GET-observed values have not been accepted by POST',
                     'POST dryRun safety/behavior not verified',
                     'No cloud writes or machine operations supported'],
    }
    return candidate, report


def build_file(spec_path: str | Path) -> tuple[dict, dict]:
    return build_report(Path(spec_path).read_bytes())
