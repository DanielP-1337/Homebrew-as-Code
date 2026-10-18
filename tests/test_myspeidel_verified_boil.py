"""Offline, deliberately incomplete mapping grounded in controlled web/API observations."""
import copy

from homebrew_as_code.myspeidel_ingredients import build_ingredient_plan, build_ingredient_plan_file
from homebrew_as_code.recipe import load_recipe

PATH = 'recipes/lebkuchen-zauber/recipe.yaml'


def test_boil_draft_timeline_and_safety():
    result = build_ingredient_plan_file(PATH)
    assert result['upload_ready'] is False and result['api_payload'] is None
    steps = result['boil_steps_offline_draft']
    assert [s['duration'] for s in steps] == [60, 10, 5]
    assert all(s['duration_meaning'] == 'minutes_before_end' for s in steps)
    assert all('ingredients' not in s['adds'] for s in steps)
    assert sum(s['duration'] for s in steps) != result['mapped_program']['boil']['boiling_duration']


def test_goldings_uses_observed_hop_shape():
    entries = build_ingredient_plan_file(PATH)['boil_steps_offline_draft'][0]['adds']['hops']
    assert len(entries) == 1
    assert entries[0]['amount'] == 60
    assert entries[0]['acid'] == 2.9
    assert entries[0]['source_category'] == 'hop'
    assert entries[0]['evidence'] == 'observed_for_hops'
    assert entries[0]['hop_uuid'] is None


def test_other_ingredients_use_explicitly_tentative_container():
    steps = build_ingredient_plan_file(PATH)['boil_steps_offline_draft']
    assert len(steps[1]['adds']['hops']) == 1  # honey at 10 min
    assert len(steps[2]['adds']['hops']) == 5  # spices at 5 min
    assert all(x['source_category'] == 'other_ingredient' for x in steps[2]['adds']['hops'])
    assert all(x['acid'] == 0 and x['hop_uuid'] is None for s in steps[1:] for x in s['adds']['hops'])
    assert all(x['evidence'] == 'observed_for_ceylon_cinnamon_only' for s in steps[1:] for x in s['adds']['hops'])


def test_timing_evidence_is_scoped_not_a_writer_contract():
    result = build_ingredient_plan_file(PATH)
    evidence = result['boil_timing_evidence']
    assert evidence['observed_web_remaining_min'] == evidence['observed_api_duration_raw']
    assert evidence['scope'] == 'three steps in one manually created test recipe'
    assert any('verify all other ingredient' in blocker.lower() for blocker in result['blocked_by'])


def test_mapping_is_deterministic_and_does_not_mutate():
    recipe = load_recipe(PATH)
    before = copy.deepcopy(recipe)
    assert build_ingredient_plan(recipe) == build_ingredient_plan(recipe)
    assert recipe == before
