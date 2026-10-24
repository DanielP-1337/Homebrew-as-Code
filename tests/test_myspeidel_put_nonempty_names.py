"""Focused offline tests for the nonempty-reference-names experiment."""
import copy
import pytest
from homebrew_as_code.myspeidel_put_experiments import make_variant


def baseline():
    return {
        'name': 'MySpeidel Roundtrip Test 001', 'recipe_type': 0,
        'references': {
            'water_types': {'water-id': {'name': None, 'uuid': 'water-id', 'mineral': 7}},
            'hops': {'hop-id': {'name': None, 'uuid': 'hop-id', 'alpha': 4}},
            'malts': {'malt-id': {'name': 'Pale Ale'}},
        },
    }


def test_nonempty_names_preserve_reference_fields_and_baseline():
    original = baseline()
    frozen = copy.deepcopy(original)
    candidate, counts = make_variant(original, 'nonempty-reference-names')
    assert original == frozen
    assert counts == {'water_types': 1, 'hops': 1}
    assert candidate['references']['water_types']['water-id'] == {
        'name': 'Test Water Reference', 'uuid': 'water-id', 'mineral': 7,
    }
    assert candidate['references']['hops']['hop-id'] == {
        'name': 'Test Hop Reference', 'uuid': 'hop-id', 'alpha': 4,
    }
    assert candidate['references']['malts'] == original['references']['malts']
    assert candidate['recipe_type'] == original['recipe_type']


def test_refuses_partial_or_noop_candidate():
    original = baseline()
    original['references']['hops']['hop-id']['name'] = 'Already populated'
    with pytest.raises(ValueError, match='Expected exactly one'):
        make_variant(original, 'nonempty-reference-names')


def test_other_variants_remain_unchanged():
    candidate, _ = make_variant(baseline(), 'empty-string-names')
    assert candidate['references']['hops']['hop-id']['name'] == ''
    candidate, _ = make_variant(baseline(), 'omit-null-names')
    assert 'name' not in candidate['references']['hops']['hop-id']
