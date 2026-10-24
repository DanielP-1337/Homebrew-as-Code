"""Tests for offline parsing of captured browser form submissions."""
import json
from urllib.parse import urlencode

import pytest

from homebrew_as_code.myspeidel_web_form_contract import (
    compare_cloud_backup, inspect_form, main,
)


def _payload():
    return urlencode([
        ('recipe[name]', 'Example – DevTools'),
        ('recipe[name]', 'Example – DevTools'),
        ('recipe[water_type_id]', ''),
        ('malts_to_recipe[0][malt_id]', 'Pale Ale Malz'),
        ('malts_to_recipe[0][amount]', '2.8'),
        ('hops_to_recipe[1][0][hop_id]', '6333'),
        ('hops_to_recipe[1][0][amount]', '11'),
        ('hops_to_recipe[1][1][hop_id]', ''),
        ('recipe[csrf_token]', 'SECRET'),
    ]).encode('utf-8')


def test_form_groups_ingredients_and_duplicate_fields():
    result = inspect_form(_payload())
    assert result['field_count'] == 9
    assert result['duplicate_field_names']['recipe[name]'] == 2
    assert result['group_counts']['recipe']['fields'] == 4
    assert result['ingredient_rows'] == [
        {'group': 'malts_to_recipe', 'index': '0', 'id_field': 'malt_id', 'id_value': 'Pale Ale Malz', 'amount': '2.8', 'acid': ''},
        {'group': 'hops_to_recipe', 'index': '1/0', 'id_field': 'hop_id', 'id_value': '6333', 'amount': '11', 'acid': ''},
    ]
    assert 'SECRET' not in json.dumps(result)


def test_cloud_comparison_does_not_guess_id_mapping():
    report = inspect_form(_payload())
    comparison = compare_cloud_backup(report, {'recipe': {'name': 'Example – DevTools', 'references': {'hops': {}}}})
    assert comparison['recipe_fields_compared']['name']['string_equal'] is True
    assert comparison['ingredient_id_mapping'] == 'unverified'


def test_reject_non_form_data():
    with pytest.raises(ValueError):
        inspect_form(b'hello=world')


def test_cli_writes_only_inside_local_and_never_overwrites(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    local = tmp_path / '.local'
    local.mkdir()
    (local / 'request.txt').write_bytes(_payload())
    args = ['--form', '.local/request.txt', '--report', '.local/report.json']
    assert main(args) == 0
    assert json.loads((local / 'report.json').read_text())['field_count'] == 9
    assert main(args) == 1


def test_cli_rejects_output_outside_local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.local').mkdir()
    (tmp_path / '.local/request.txt').write_bytes(_payload())
    assert main(['--form', '.local/request.txt', '--report', 'public.json']) == 1


def test_source_size_limit():
    with pytest.raises(ValueError):
        inspect_form(b'recipe[name]=x' * 200000)
