import json
from copy import deepcopy

import pytest

from homebrew_as_code.bridge_export import build_bridge_export, main
from homebrew_as_code.recipe import RecipeError, load_recipe

SOURCE = 'recipes/lebkuchen-zauber/recipe.yaml'


def test_mapping_and_losses():
    doc, report = build_bridge_export([load_recipe(SOURCE)])
    recipe = doc['recipes'][0]
    assert set(doc) == {'recipes'}
    assert recipe == {'name': 'Lebkuchen-Zaub', 'mash_in_temperature': 60,
                      'rests': [{'temperature': 63, 'minutes': 20},
                                {'temperature': 72, 'minutes': 45},
                                {'temperature': 78, 'minutes': 10}],
                      'boil_minutes': 60, 'boil_temperature': 100, 'hop_additions': [60]}
    assert len(report['recipes'][0]['warnings']) == 7
    assert report['replaces_all_device_recipes'] is True


@pytest.mark.parametrize('field,value', [('temperature_c', 94), ('temperature_c', 100.5),
                                        ('duration_min', 181), ('duration_min', True),
                                        ('duration_min', float('nan'))])
def test_reject_unrepresentable_boil(field, value):
    recipe = load_recipe(SOURCE)
    recipe['boil'][field] = value
    with pytest.raises(RecipeError):
        build_bridge_export([recipe])


def test_capacity_and_hop_bounds():
    recipe = load_recipe(SOURCE)
    for count in (0, 10):
        with pytest.raises(RecipeError):
            build_bridge_export([recipe] * count)
    doc, _ = build_bridge_export([recipe] * 9)
    assert len(doc['recipes']) == 9
    for count in (6, 7):
        changed = deepcopy(recipe)
        changed['boil']['additions'] = [recipe['boil']['additions'][0]] * count
        if count == 6:
            assert len(build_bridge_export([changed])[0]['recipes'][0]['hop_additions']) == 6
        else:
            with pytest.raises(RecipeError):
                build_bridge_export([changed])
    recipe['boil']['additions'][0]['remaining_min'] = 0
    with pytest.raises(RecipeError):
        build_bridge_export([recipe])


def test_names_and_no_mutation():
    recipe = load_recipe(SOURCE)
    recipe['recipe']['name'] = 'Märzen; süß'
    before = deepcopy(recipe)
    assert build_bridge_export([recipe])[0]['recipes'][0]['name'] == 'Maerzen suess'
    assert recipe == before


def test_cli_and_failure_no_output(tmp_path):
    output = tmp_path / 'bridge.json'
    assert main([SOURCE, '-o', str(output)]) == 0
    assert json.loads(output.read_text())['recipes'][0]['hop_additions'] == [60]
    assert output.with_suffix('.report.json').exists()
    invalid = tmp_path / 'invalid.json'
    assert main([SOURCE] * 10 + ['-o', str(invalid)]) == 1
    assert not invalid.exists()
