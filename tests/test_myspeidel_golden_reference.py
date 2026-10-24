"""Synthetic fixtures only: vendor samples remain outside git."""
import json
from homebrew_as_code.myspeidel_golden_reference import inspect
from homebrew_as_code.myspeidel_golden_reference_cli import main


def fixture():
    return {'openapi': '3.0.3', 'components': {
        'schemas': {'recipe_v5': {'type': 'object', 'required': ['name', 'public'], 'properties': {'name': {'type': 'string'}, 'public': {'type': 'boolean'}}}},
        'examples': {'recipe': {'value': {'name': 'Test', 'uuid': 'SYNTHETIC'}}},
        'parameters': {'dryRun': {'name': 'dryRun', 'in': 'query', 'schema': {'type': 'boolean'}}}},
    'paths': {'/v1.0/recipe': {'post': {'parameters': [{'$ref': '#/components/parameters/dryRun'}], 'requestBody': {'content': {'application/json': {'schema': {'oneOf': [{'$ref': '#/components/schemas/recipe_v5'}]}}}}}},
              '/v1.0/recipe/{uuid}': {'get': {'responses': {'200': {'content': {'application/json': {'schema': {'$ref': '#/components/schemas/recipe_v5'}}}}}}}}}


def test_reports_missing_and_does_not_copy_values():
    report = inspect(json.dumps(fixture()).encode())
    assert report['example_missing_required'] == ['public']
    assert report['upload_ready'] is False and report['api_payload'] is None
    assert 'SYNTHETIC' not in json.dumps(report)


def test_post_get_refs_and_dryrun():
    report = inspect(json.dumps(fixture()).encode())
    assert report['dryrun_documented']
    assert report['post_schema_refs'] == ['#/components/schemas/recipe_v5']
    assert report['get_schema_ref'] == '#/components/schemas/recipe_v5'


def test_invalid_ref_fails():
    import pytest
    obj = fixture()
    obj['components']['examples']['recipe'] = {'$ref': '#/missing'}
    with pytest.raises(ValueError):
        inspect(json.dumps(obj).encode())


def test_bad_spec_version_fails():
    import pytest
    obj = fixture(); obj['openapi'] = '2.0'
    with pytest.raises(ValueError):
        inspect(json.dumps(obj).encode())


def test_cli_refuses_overwrite(tmp_path):
    spec = tmp_path / 'spec.json'; dest = tmp_path / 'report.json'
    spec.write_text(json.dumps(fixture()), encoding='utf8')
    assert main(['--spec', str(spec), '--output', str(dest)]) == 0
    assert main(['--spec', str(spec), '--output', str(dest)]) == 1
    assert json.loads(dest.read_text())['upload_ready'] is False
