"""Offline ingredient mapping tests using repository-owned recipe only."""
import copy
import json

import pytest

from homebrew_as_code.myspeidel_ingredients import build_ingredient_plan, build_ingredient_plan_file
from homebrew_as_code.myspeidel_ingredients_cli import main
from homebrew_as_code.myspeidel_mapper import MappingError
from homebrew_as_code.recipe import load_recipe

PATH = 'recipes/lebkuchen-zauber/recipe.yaml'


def test_ingredient_plan_units_and_count():
    plan = build_ingredient_plan_file(PATH)
    assert plan['upload_ready'] is False and plan['api_payload'] is None
    assert len(plan['malts']) == 5
    assert [i['amount_kg'] for i in plan['malts']] == [2.8, 1.5, .45, .25, .1]
    assert all(i['catalog_uuid'] is None for i in plan['malts'])


def test_hop_times_are_web_form_only():
    plan = build_ingredient_plan_file(PATH)
    schedule = plan['boil_additions_web_form_timeline']
    assert [item['minutes_before_end'] for item in schedule] == [60.0, 10.0, 5.0]
    hop = schedule[0]['hops'][0]
    assert hop['amount_g'] == 60.0 and hop['alpha_acid_percent'] == 2.9
    assert len(schedule[2]['other_ingredients']) == 5
    assert len(schedule[1]['other_ingredients']) == 1
    assert 'steps' not in plan['mapped_program']['boil']


def test_manifest_is_deterministic_and_non_mutating():
    recipe = load_recipe(PATH)
    before = copy.deepcopy(recipe)
    assert build_ingredient_plan(recipe) == build_ingredient_plan(recipe)
    assert recipe == before


def test_rejects_falling_mash_rest():
    recipe = load_recipe(PATH)
    recipe['mash']['steps'][1]['temperature_c'] = 61
    with pytest.raises(MappingError, match='nondecreasing'):
        build_ingredient_plan(recipe)


def test_rejects_overlong_boil():
    recipe = load_recipe(PATH)
    recipe['boil']['duration_min'] = 181
    with pytest.raises(MappingError, match='180'):
        build_ingredient_plan(recipe)


def test_rejects_invalid_hop_acid():
    recipe = load_recipe(PATH)
    recipe['boil']['additions'][0]['alpha_acid_percent'] = 101
    with pytest.raises(MappingError, match='100'):
        build_ingredient_plan(recipe)


def test_rejects_missing_ingredient_amount():
    recipe = load_recipe(PATH)
    recipe['boil']['additions'][1].pop('amount_g')
    with pytest.raises(MappingError, match='finite'):
        build_ingredient_plan(recipe)


def test_cli_offline(capsys, monkeypatch):
    monkeypatch.delenv('MYSPEIDEL_TOKEN', raising=False)
    assert main([PATH]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['upload_ready'] is False and result['api_payload'] is None


def test_cli_missing_file(capsys):
    assert main(['nonexistent.yaml']) == 1
    assert 'ERROR' in capsys.readouterr().err
