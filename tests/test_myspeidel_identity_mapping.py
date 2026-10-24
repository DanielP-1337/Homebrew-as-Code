"""Offline candidate matching: deliberately not proof of ingredient identity."""
from homebrew_as_code.myspeidel_identity_mapping import inspect_mapping, _cloud_occurrences


def _form():
    return {'recipe_fields': {'name': 'Example'}, 'ingredient_rows': [
        {'group': 'hops_to_recipe', 'index': '1/0', 'id_value': '6333', 'amount': '11', 'acid': '5'},
        {'group': 'hops_to_recipe', 'index': '2/0', 'id_value': '6333', 'amount': '7', 'acid': '5'},
        {'group': 'hops_to_recipe', 'index': '3/0', 'id_value': '139980', 'amount': '5', 'acid': '0'},
    ]}


def test_repeated_web_id_consistency():
    recipe = {'name': 'Example', 'references': {'hops': {'XYZ': {'hop_uuid': 'fake'}}},
              'boil': {'steps': [
                  {'adds': {'hops': [{'hop_uuid': 'UUID_A', 'amount': 11, 'acid': 5}]}},
                  {'adds': {'hops': [{'hop_uuid': 'UUID_A', 'amount': 7, 'acid': 5}]}},
                  {'adds': {'hops': [{'hop_uuid': 'UUID_B', 'amount': 5, 'acid': 0}]}},
              ]}}
    report = inspect_mapping(_form(), recipe)
    assert [row['status'] for row in report['mappings']] == ['CANDIDATE'] * 3
    assert [row['candidate_cloud_uuids'] for row in report['mappings']] == [['UUID_A'], ['UUID_A'], ['UUID_B']]
    assert report['verified_mapping_count'] == 0
    assert len(_cloud_occurrences(recipe)) == 3


def test_colliding_amounts_are_ambiguous():
    form = {'recipe_fields': {}, 'ingredient_rows': [
        {'group': 'hops_to_recipe', 'index': '1/0', 'id_value': '123', 'amount': '5', 'acid': ''}]}
    recipe = {'boil': {'steps': [{'adds': {'hops': [
        {'hop_uuid': 'A', 'amount': 5}, {'hop_uuid': 'B', 'amount': 5}]}}]}}
    assert inspect_mapping(form, recipe)['mappings'][0]['status'] == 'AMBIGUOUS'


def test_missing_value_unresolved():
    form = {'recipe_fields': {}, 'ingredient_rows': [
        {'group': 'malts_to_recipe', 'index': '0', 'id_value': 'Pale Ale', 'amount': '2.8'}]}
    assert inspect_mapping(form, {'references': {'malts': {'A': {'malt_uuid': 'A'}}}})['mappings'][0]['status'] == 'UNRESOLVED'


def test_mismatched_acid_not_assumed_equal():
    form = {'recipe_fields': {}, 'ingredient_rows': [
        {'group': 'hops_to_recipe', 'index': '1/0', 'id_value': '1', 'amount': '5', 'acid': '4'}]}
    recipe = {'boil': {'steps': [{'adds': {'hops': [{'hop_uuid': 'A', 'amount': 5, 'acid': 6}]}}]}}
    assert inspect_mapping(form, recipe)['mappings'][0]['status'] == 'UNRESOLVED'
