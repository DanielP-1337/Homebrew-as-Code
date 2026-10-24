import io
import json
import urllib.error

import pytest

from homebrew_as_code.myspeidel_put_roundtrip import (
    PutDiagnosticError, put_recipe, safe_schema_path, safe_validation_paths,
)

UUID = '123e4567-e89b-12d3-a456-426614174000'
RECIPE = {'uuid': UUID, 'public': 0, 'machine_type': {'size': 20}}


def test_allowlisted_paths():
    assert safe_schema_path('$.boil.steps[2].adds.hops[0].hop_uuid') == '$.boil.steps[2].adds.hops[0].hop_uuid'
    assert safe_schema_path('/mashing/adds/malts/0/malt_uuid') is None
    assert safe_schema_path('body.uuid') == '$.uuid'
    assert safe_schema_path('$.references.malts.26960.uuid') is None
    assert safe_schema_path('$.owner.secret') is None
    assert safe_schema_path('$.owner.uuid;token=ABC') is None


def test_bounded_unique_paths_and_no_echo():
    data = {'message': 'SECRET', 'errors': [
        {'path': '$.mashing.adds.malts[0].malt_uuid', 'message': 'PRIVATE'},
        {'path': '$.mashing.adds.malts[0].malt_uuid'},
        {'path': '$.references.hops.20436.uuid', 'message': 'PRIVATE'},
        {'path': '$.public'},
    ]}
    assert safe_validation_paths(json.dumps(data).encode()) == (
        '$.mashing.adds.malts[0].malt_uuid', '$.public')
    assert safe_validation_paths(b'<html>PRIVATE</html>') == ()


def test_put_error_includes_only_safe_paths():
    body = json.dumps({'errors': [
        {'path': '$.rest.steps[0].duration', 'message': 'PRIVATE SECRET'},
        {'path': '$.references.malts.26960.uuid', 'message': 'SECRET'},
    ]}).encode()
    def opener(*args, **kwargs):
        raise urllib.error.HTTPError('https://redacted', 400, 'error', {}, io.BytesIO(body))
    with pytest.raises(PutDiagnosticError) as info:
        put_recipe('token', UUID, RECIPE, dry_run=True, opener=opener)
    assert info.value.paths == ('$.rest.steps[0].duration',)
    assert 'PRIVATE' not in repr(info.value.paths)


def test_offline_compare_is_value_free(tmp_path, monkeypatch):
    from homebrew_as_code.myspeidel_put_offline_schema import compare_backup
    from homebrew_as_code.myspeidel_put_roundtrip import digest
    monkeypatch.chdir(tmp_path)
    local = tmp_path / '.local'
    local.mkdir()
    backup = local / 'backup.json'
    backup.write_text(json.dumps({
        'format': 'homebrew-as-code/myspeidel-put-backup-v1',
        'uuid': UUID, 'recipe': RECIPE, 'sha256': digest(RECIPE),
    }), encoding='utf-8')
    spec = local / 'spec.json'
    spec.write_text(json.dumps({'components': {'schemas': {
        'recipe_v4': {'type': 'object', 'required': ['name'], 'properties': {'name': {'type': 'string'}}},
        'recipe_v5': {'type': 'object', 'properties': {'public': {'type': 'integer'}}},
    }}}), encoding='utf-8')
    report = compare_backup(str(spec), str(backup))
    assert report['offline'] is True and report['upload_ready'] is False
    assert report['results'][0]['first_errors'] == [{'path': '$.name', 'code': 'required_missing'}]
    assert UUID not in json.dumps(report)
