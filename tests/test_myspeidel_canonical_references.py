"""Offline canonical catalog resolution does not mutate recipe IDs or shared records."""
import copy
import pytest
from homebrew_as_code.myspeidel_canonical_references import catalog_get_paths, resolve


def fixture():
    recipe = {'mashing': {'adds': {'water': {'uuid': 'W1'}}},
              'boil': {'steps': [{'adds': {'hops': [{'hop_uuid': 'H1'}]}}]},
              'references': {'water_types': {'W1': {'name': None, 'owner_uuid': 'O'}},
                             'hops': {'H1': {'name': None}}, 'malts': {'M1': {'name': 'Malt'}}}}
    catalog = {'water_types': {'W1': {'name': 'Water', 'owner_uuid': 'O'}},
               'hops': {'H1': {'name': 'Hop'}}}
    return recipe, catalog


def test_replaces_only_null_names_and_keeps_source_untouched():
    recipe, catalog = fixture()
    old, old_catalog = copy.deepcopy(recipe), copy.deepcopy(catalog)
    candidate, diagnostics = resolve(recipe, catalog)
    assert recipe == old and catalog == old_catalog
    assert candidate['mashing'] == recipe['mashing']
    assert candidate['boil'] == recipe['boil']
    assert candidate['references']['water_types']['W1']['name'] == 'Water'
    assert candidate['references']['hops']['H1']['name'] == 'Hop'
    assert diagnostics['hops']['resolved_null_names'] == 1


def test_missing_canonical_uuid_not_fabricated():
    recipe, catalog = fixture()
    del catalog['hops']['H1']
    candidate, diagnostics = resolve(recipe, catalog)
    assert candidate['references']['hops']['H1']['name'] is None
    assert diagnostics['hops']['missing_canonical_records'] == 1


def test_conflicting_field_never_overwritten():
    recipe, catalog = fixture()
    catalog['water_types']['W1']['owner_uuid'] = 'OTHER'
    candidate, diagnostics = resolve(recipe, catalog)
    assert candidate['references']['water_types']['W1']['owner_uuid'] == 'O'
    assert diagnostics['water_types']['different_existing_fields'] == 1


def test_empty_catalog_name_rejected():
    recipe, catalog = fixture()
    catalog['hops']['H1']['name'] = ''
    with pytest.raises(ValueError, match='name'):
        resolve(recipe, catalog)


def test_routes_only_from_actual_spec():
    assert catalog_get_paths({'paths': {'/v1.0/hops': {'get': {}}, '/v1.0/recipe': {'put': {}}, '/users': {'get': {}}}}) == [
        {'method': 'GET', 'path': '/v1.0/hops'}]
