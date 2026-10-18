import csv
import io
import json
from copy import deepcopy
from pathlib import Path
import pytest
from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.shopping_export import build_request, build_shopware_cart_preview, export_texts
from homebrew_as_code.shopping_cli import main

RECIPE = str(Path(__file__).resolve().parents[1] / 'recipes/lebkuchen-zauber/recipe.yaml')


def test_complete_bom_and_no_guess():
    data = build_request(load_recipe(RECIPE))
    assert len(data['items']) == 15  # 5 malts + 7 boil + yeast + 2 salts
    assert sum(x['whole_grain_required'] for x in data['items']) == 5
    assert all(x['shopware_product_id'] is None for x in data['items'])
    assert data['order_submitted'] is False
    assert build_shopware_cart_preview(data)['ready'] is False


def test_known_pack_roundup():
    data = build_request(load_recipe(RECIPE), catalog={'CaraMunich II': {'sku': 'example-sku', 'pack_g': 500, 'shopware_product_id': 'a' * 32}})
    row = next(x for x in data['items'] if x['name'] == 'CaraMunich II')
    assert row['required_g'] == 450 and row['purchase_quantity'] == 1
    assert data['order_submitted'] is False


def test_preview_all_or_nothing():
    recipe = load_recipe(RECIPE)
    catalog = {x['name']: {'sku': 'test', 'pack_g': 100, 'shopware_product_id': f'{i+1:032x}'}
               for i, x in enumerate(build_request(recipe)['items'])}
    doc = build_request(recipe, catalog=catalog)
    preview = build_shopware_cart_preview(doc)
    assert preview['ready'] is True
    assert preview['transmitted'] is False
    assert len(preview['request']['lineItems']) == 15
    assert preview['request']['lineItems'][0]['quantity'] == 28


def test_refuses_invalid_catalog_ids_and_pack():
    recipe = load_recipe(RECIPE)
    with pytest.raises(ValueError):
        build_request(recipe, catalog={'Pale Ale Malt': {'shopware_product_id': 'fake'}})
    with pytest.raises(ValueError):
        build_request(recipe, catalog={'Pale Ale Malt': {'pack_g': 0}})


def test_csv_and_json():
    a, b, c = export_texts(load_recipe(RECIPE))
    assert len(json.loads(a)['items']) == 15
    assert len(list(csv.DictReader(io.StringIO(b), delimiter=';'))) == 15
    assert json.loads(c)['request'] is None


def test_cli_writes_only_on_demand(tmp_path):
    prefix = tmp_path / 'rfq'
    assert main([RECIPE, '--output-prefix', str(prefix)]) == 0
    assert prefix.with_suffix('.rfq.csv').exists()
    assert main([RECIPE, '--output-prefix', str(prefix)]) == 1
