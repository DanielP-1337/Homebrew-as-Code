"""Privacy regression tests for MySpeidel offline error paths."""
from homebrew_as_code.myspeidel_put_offline_schema import _safe_structural_path


def _schema():
    user = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
    item = {'type': 'object', 'properties': {'name': {'type': 'string'}, 'owner_uuid': {'type': 'string'}}}
    return {'type': 'object', 'properties': {
        'owner': user, 'brewer': user,
        'references': {'type': 'object', 'properties': {
            'water_types': {'type': 'object', 'additionalProperties': item},
            'hops': {'type': 'object', 'additionalProperties': item},
        }},
        'mashing': {'type': 'object', 'properties': {'adds': {'type': 'object', 'properties': {
            'malts': {'type': 'array', 'items': item}
        }}}},
    }}


def test_regular_and_dynamic_paths():
    spec = {'components': {'schemas': {}}}
    schema = _schema()
    assert _safe_structural_path(spec, schema, '$.owner.name') == '$.owner.name'
    assert _safe_structural_path(spec, schema, '$.brewer.name') == '$.brewer.name'
    assert _safe_structural_path(spec, schema, '$.references.water_types.PRIVATE-ID.name') == '$.references.water_types.<redacted>.name'
    assert _safe_structural_path(spec, schema, '$.references.hops.SECRET-ID.name') == '$.references.hops.<redacted>.name'
    assert _safe_structural_path(spec, schema, '$.mashing.adds.malts[314].name') == '$.mashing.adds.malts[*].name'


def test_unverified_segments_never_leak():
    spec = {'components': {'schemas': {}}}
    schema = _schema()
    assert _safe_structural_path(spec, schema, '$.owner.SECRET') == 'redacted'
    assert _safe_structural_path(spec, schema, '$.references.hops.SECRET-ID') == '$.references.hops.<redacted>'
    assert _safe_structural_path(spec, schema, '$.secret.ABC') == 'redacted'
    assert _safe_structural_path(spec, schema, '$.mashing.adds.malts[4].SECRET') == 'redacted'


def test_invalid_and_recursive_refs():
    spec = {'components': {'schemas': {'Node': {'$ref': '#/components/schemas/Node'}}}}
    assert _safe_structural_path(spec, {'$ref': '#/components/schemas/Node'}, '$.name') == 'redacted'
    assert _safe_structural_path(spec, _schema(), '$.references.hops[0].name') == 'redacted'
    assert _safe_structural_path(spec, _schema(), 'malicious') == 'redacted'
