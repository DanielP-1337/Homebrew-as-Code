"""Type-only diagnostics never export private property values or map identifiers."""
import json

from homebrew_as_code.myspeidel_put_offline_schema import _type_diagnostic, _json_type


def test_type_labels_are_data_free():
    assert _json_type(None) == 'null'
    assert _json_type(True) == 'boolean'
    assert _json_type(7) == 'integer'
    assert _json_type('PRIVATE') == 'string'


def test_reference_resolution_and_nested_types():
    spec = {'components': {'schemas': {
        'ref': {'type': 'string'},
    }}}
    schema = {'type': 'object', 'properties': {'malts': {
        'type': 'array', 'items': {'type': 'object', 'properties': {
            'uuid': {'$ref': '#/components/schemas/ref'},
        }},
    }}}
    recipe = {'malts': [{'uuid': None}]}
    result = _type_diagnostic(spec, schema, recipe, '$.malts[0].uuid')
    assert result == {'expected': 'string', 'actual': 'null', 'nullable': False}
    assert 'uuid' not in json.dumps(result)


def test_dynamic_reference_map_key_never_in_output():
    spec = {'components': {'schemas': {}}}
    schema = {'type': 'object', 'properties': {'references': {
        'type': 'object', 'additionalProperties': {
            'type': 'object', 'properties': {'uuid': {'type': 'string'}}
        }
    }}}
    recipe = {'references': {'PRIVATE_123': {'uuid': 6}}}
    result = _type_diagnostic(spec, schema, recipe, '$.references.PRIVATE_123.uuid')
    assert result['expected'] == 'string'
    assert result['actual'] == 'integer'
    assert 'PRIVATE_123' not in json.dumps(result)
