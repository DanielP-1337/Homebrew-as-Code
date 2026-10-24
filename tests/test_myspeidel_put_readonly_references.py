"""0019y reference omission variants never mutate the input recipe."""
import copy
import pytest

from homebrew_as_code.myspeidel_put_experiments import make_variant


@pytest.fixture
def recipe():
    return {
        'name': 'Private test', 'recipe_type': 0,
        'mashing': {'steps': [{'adds': {'malts': [{'malt_uuid': 'MALT-A'}]}}]},
        'boil': {'steps': [{'adds': {'hops': [{'hop_uuid': 'HOP-A'}]}}]},
        'references': {
            'water_types': {'WATER-A': {'name': None, 'owner_uuid': 'OWNER-A'}},
            'hops': {'HOP-A': {'name': None, 'owner_uuid': 'OWNER-A'}},
            'malts': {'MALT-A': {'name': 'Pale'}},
            'other_scalar': 7,
        },
    }


@pytest.mark.parametrize('variant', ['omit-references', 'empty-references', 'empty-reference-categories'])
def test_variant_does_not_mutate_source_or_brewing_step_ids(recipe, variant):
    original = copy.deepcopy(recipe)
    candidate, counts = make_variant(recipe, variant)
    assert recipe == original
    assert candidate is not recipe
    assert candidate['mashing'] == recipe['mashing']
    assert candidate['boil'] == recipe['boil']
    assert all(value == 0 for value in counts.values())
    if variant == 'omit-references':
        assert 'references' not in candidate
    elif variant == 'empty-references':
        assert candidate['references'] == {}
    else:
        assert candidate['references'] == {
            'water_types': {}, 'hops': {}, 'malts': {}, 'other_scalar': 7,
        }


def test_variants_reject_missing_references(recipe):
    del recipe['references']
    for variant in ('omit-references', 'empty-references', 'empty-reference-categories'):
        with pytest.raises(ValueError, match='Missing references'):
            make_variant(recipe, variant)


def test_ids_only_rejects_no_op(recipe):
    recipe['references'] = {'hops': {}, 'water_types': {}}
    with pytest.raises(ValueError, match='No reference entries'):
        make_variant(recipe, 'empty-reference-categories')


def test_original_experiment_remains_unchanged(recipe):
    candidate, _ = make_variant(recipe, 'original')
    assert candidate == recipe
    assert candidate is not recipe
