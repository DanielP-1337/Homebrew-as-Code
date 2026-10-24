"""Supplier separation must be exhaustive, explicit, and safe."""
import csv
import io
import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.supplier_split import split_request, render_split
from homebrew_as_code.supplier_split_cli import main

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes/lebkuchen-zauber/recipe.yaml'
CATALOG = ROOT / 'catalogs/braupartner.verified.yaml'


def loaded():
    return load_recipe(RECIPE), yaml.safe_load(CATALOG.read_text(encoding='utf-8'))


def test_all_15_items_are_partitioned_without_overlap():
    r, c = loaded()
    parts, report = split_request(r, c)
    assert report['counts'] == {'brewshop': 7, 'grocery': 6, 'water_chemistry': 2}
    assert report['total_positions'] == 15
    assert report['brewshop_documented_offers'] == 7
    names = [item['ingredient'] for part in parts.values() for item in part['positions']]
    assert len(names) == len(set(names)) == 15


def test_braupartner_receives_no_supermarket_or_salts():
    parts, report = split_request(*loaded())
    brew = parts['brewshop']
    assert brew['supplier'] == 'braupartner.de'
    assert all(x['category'] in ('malt', 'hop', 'yeast') for x in brew['positions'])
    assert not brew['order_submitted'] and not report['automatic_checkout_enabled']
    assert next(x for x in brew['positions'] if x['ingredient'] == 'Pale Ale Malt')['requested_g'] == 3000


def test_grocery_and_pharmacy_are_not_fictional_vendor_offers():
    parts, _ = split_request(*loaded())
    for part in (parts['grocery'], parts['water_chemistry']):
        assert part['supplier'] is None
        assert all(x['supplier_sku'] is None and x['source_url'] is None for x in part['positions'])
        assert part['document_type'] == 'PURCHASE_PLANNING_ONLY'
    assert 'Dihydrat' in parts['water_chemistry']['positions'][0]['purchase_description']


def test_unknown_ingredient_is_rejected_not_silently_routed():
    recipe, catalog = loaded()
    recipe = deepcopy(recipe)
    recipe['boil']['additions'].append({'ingredient': 'Special surprise spice', 'amount_g': 2, 'remaining_min': 5})
    with pytest.raises(ValueError, match='Unclassified'):
        split_request(recipe, catalog)


def test_exports_keep_csv_rows_and_safe_markdown():
    files = render_split(*loaded())
    assert len(files) == 10
    assert len(list(csv.DictReader(io.StringIO(files['.grocery.csv']), delimiter=';'))) == 6
    assert len(list(csv.DictReader(io.StringIO(files['.brewshop.csv']), delimiter=';'))) == 7
    assert 'Ceylon' not in files['.brewshop.md']
    assert 'CaCl2' in files['.water_chemistry.md']
    assert json.loads(files['.split-report.json'])['total_positions'] == 15


def test_cli_refuses_overwrite(tmp_path):
    prefix = tmp_path / 'suppliers'
    args = [str(RECIPE), '--catalog', str(CATALOG), '--output-prefix', str(prefix)]
    assert main(args) == 0
    assert (tmp_path / 'suppliers.brewshop.md').is_file()
    assert main(args) == 1
