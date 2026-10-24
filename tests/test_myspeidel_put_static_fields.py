"""Static schema-property names only, never dynamic reference IDs."""
from homebrew_as_code.myspeidel_put_offline_schema import _safe_static_field


def test_nested_known_property_after_dynamic_key():
    spec = {'components': {'schemas': {'Ref': {'type': 'string'}}}}
    schema = {'type': 'object', 'properties': {'references': {
        'type': 'object', 'properties': {'malts': {
            'type': 'object', 'additionalProperties': {
                'type': 'object', 'properties': {'owner_uuid': {'$ref': '#/components/schemas/Ref'}}
            }
        }}
    }}}
    path = '$.references.malts.SECRET_IDENTIFIER.owner_uuid'
    assert _safe_static_field(spec, schema, path) == 'owner_uuid'
    assert _safe_static_field(spec, schema, '$.references.malts.owner_uuid') == 'redacted'
    assert _safe_static_field(spec, schema, '$.references.malts.SECRET_IDENTIFIER') == 'redacted'


def test_unknown_or_dynamic_leaf_is_redacted():
    spec = {'components': {'schemas': {}}}
    schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
    assert _safe_static_field(spec, schema, '$.name') == 'name'
    assert _safe_static_field(spec, schema, '$.SECRET') == 'redacted'
    assert _safe_static_field(spec, schema, '$.abc[0]') == 'redacted'
