"""Only synthetic reference fixtures: no vendor samples or private data in Git."""
import json
from pathlib import Path

from homebrew_as_code.myspeidel_golden_validation import build_report
from homebrew_as_code.myspeidel_golden_validation_cli import main


def spec():
    return {'openapi': '3.0.3', 'components': {
        'examples': {'recipe': {'value': {'name': 'SYNTHETIC_PRIVATE_VALUE', 'mashing': {'adds': {'malts': [{'malt_uuid': 'SYNTHETIC-UUID'}]}}}}},
        'schemas': {'public': {'type': 'integer', 'minimum': 0, 'maximum': 1},
                    'recipe_v5': {'type': 'object', 'required': ['name', 'public', 'recipe_type', 'water_plato', 'mashing'],
                                  'properties': {'name': {'type': 'string'}, 'public': {'$ref': '#/components/schemas/public'},
                                                 'recipe_type': {'type': 'integer', 'minimum': 0, 'maximum': 1},
                                                 'water_plato': {'type': 'number', 'nullable': True},
                                                 'mashing': {'type': 'object', 'required': ['adds'], 'properties': {
                                                     'adds': {'type': 'object', 'properties': {'malts': {'type': 'array', 'items': {
                                                         'type': 'object', 'required': ['malt_uuid'], 'properties': {'malt_uuid': {'type': 'string'}}}}}}}}}}}}}


def test_derived_candidate_and_no_private_value_in_report():
    candidate, report = build_report(json.dumps(spec()).encode())
    assert (candidate['public'], candidate['recipe_type'], candidate['water_plato']) == (0, 0, 12)
    assert report['schema_check_passed'] is True
    assert report['upload_ready'] is False and report['api_payload'] is None
    assert 'SYNTHETIC_PRIVATE_VALUE' not in json.dumps(report)
    assert 'SYNTHETIC-UUID' not in json.dumps(report)


def test_nested_missing_required_produces_path():
    obj = spec()
    del obj['components']['examples']['recipe']['value']['mashing']['adds']['malts'][0]['malt_uuid']
    _, report = build_report(json.dumps(obj).encode())
    assert {'path': '$.mashing.adds.malts[0].malt_uuid', 'code': 'required_missing'} in report['schema_errors']


def test_reference_range_violation():
    obj = spec()
    obj['components']['schemas']['public']['maximum'] = -1
    _, report = build_report(json.dumps(obj).encode())
    assert {'path': '$.public', 'code': 'maximum'} in report['schema_errors']


def test_unknown_validation_keyword_blocks_success():
    obj = spec()
    obj['components']['schemas']['recipe_v5']['properties']['name']['contentEncoding'] = 'base64'
    _, report = build_report(json.dumps(obj).encode())
    assert report['schema_check_passed'] is False
    assert any(x['code'].startswith('unknown_keyword') for x in report['unverified_constraints'])


def test_cli_private_output_and_no_overwrites(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.local').mkdir()
    s = tmp_path / '.local' / 'spec.json'
    s.write_text(json.dumps(spec()), encoding='utf-8')
    args = ['--spec', str(s), '--candidate', '.local/candidate.json', '--report', '.local/report.json']
    assert main(args) == 0
    assert main(args) == 1
    assert json.loads((tmp_path / '.local' / 'report.json').read_text())['upload_ready'] is False
    assert main(['--spec', str(s), '--candidate', 'unsafe.json', '--report', '.local/other.json']) == 1
