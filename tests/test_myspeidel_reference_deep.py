"""Synthetic examples only; do not distribute the vendor reference fixture."""
import json
from pathlib import Path

import pytest

from homebrew_as_code.myspeidel_reference_deep import inspect_deep, inspect_deep_files
from homebrew_as_code.myspeidel_reference_deep_cli import main
from homebrew_as_code.recipe import load_recipe

RECIPE = Path(__file__).resolve().parents[1] / 'recipes/lebkuchen-zauber/recipe.yaml'


def spec():
    ref = {'$ref': '#/components/schemas/recipe_v5'}
    return {'openapi': '3.0.3', 'components': {'schemas': {
        'recipe_v5': {'type': 'object', 'required': ['name', 'uuid', 'boil'],
                      'properties': {'name': {'type': 'string'}, 'uuid': {'type': 'string'},
                                     'boil': {'$ref': '#/components/schemas/boil'},
                                     'phases': {'type': 'array', 'items': {'type': 'object', 'properties': {'kind': {'type': 'string', 'enum': ['synthetic']}}}}}},
        'boil': {'type': 'object', 'required': ['steps'], 'properties': {'steps': {
            'type': 'array', 'items': {'type': 'object', 'properties': {'duration': {'type': 'integer'}}}}}}},
        'examples': {'recipe': {'value': {'name': 'PRIVATE SYNTHETIC EXAMPLE', 'boil': {'steps': [{'duration': 5}]}}}}},
        'paths': {'/v1.0/recipe': {'post': {'parameters': [{'name': 'dryRun'}],
            'requestBody': {'content': {'application/json': {'schema': {'oneOf': [ref]}}}}}},
                  '/v1.0/recipe/{uuid}': {'get': {'responses': {'200': {'content': {'application/json': {'schema': ref}}}}}}}}


def test_report_no_leak_and_blocked():
    r = inspect_deep(spec(), load_recipe(RECIPE))
    assert r['upload_ready'] is False and r['api_payload'] is None
    assert 'PRIVATE SYNTHETIC EXAMPLE' not in json.dumps(r)
    assert r['post_get_share_recipe_v5'] is True
    assert r['example_missing_required'] == ['uuid']


def test_nested_inspection_and_types():
    r = inspect_deep(spec(), load_recipe(RECIPE))
    rows = r['nested_schema']['boil']
    assert any(x['path'] == '$.boil.steps[].duration' and x['types'] == ['integer'] for x in rows)
    assert next(x for x in rows if x['path'] == '$.boil.steps')['required_in_parent'] is True
    assert 'dryRun' in r['post_parameters']


def test_no_fabricated_identity_semantics():
    r = inspect_deep(spec(), load_recipe(RECIPE))
    uuid = next(f for f in r['fields'] if f['field'] == 'uuid')
    assert uuid['classification'] == 'UNKNOWN_POST_SEMANTICS'
    assert uuid['required'] is True


def test_missing_spec_structure_fails():
    bad = spec()
    del bad['components']['examples']['recipe']
    with pytest.raises(ValueError):
        inspect_deep(bad, load_recipe(RECIPE))


def test_file_cli_and_no_overwrite(tmp_path):
    source = tmp_path/'spec.json'
    source.write_text(json.dumps(spec()), encoding='utf-8')
    target = tmp_path/'report.json'
    assert main([str(RECIPE), '--spec', str(source), '--output', str(target)]) == 0
    report = json.loads(target.read_text(encoding='utf-8'))
    assert len(report['source_sha256']) == 64
    assert main([str(RECIPE), '--spec', str(source), '--output', str(target)]) == 1


def test_invalid_operation_ref_fails():
    bad = spec()
    bad['paths']['/v1.0/recipe']['post']['requestBody']['content']['application/json']['schema'] = {'type': 'object'}
    with pytest.raises(ValueError, match='POST or GET'):
        inspect_deep(bad, load_recipe(RECIPE))
