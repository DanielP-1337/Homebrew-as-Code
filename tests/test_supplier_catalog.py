import json
from pathlib import Path

import pytest
import yaml

from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.supplier_catalog import resolve_catalog
from homebrew_as_code.supplier_catalog_cli import main
from homebrew_as_code.shopping_export import build_request, build_shopware_cart_preview

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes/lebkuchen-zauber/recipe.yaml'


def test_empty_supplier_template_has_all_unmapped():
    source = yaml.safe_load((ROOT / 'catalogs/braupartner.example.yaml').read_text(encoding='utf-8'))
    mapping, report = resolve_catalog(load_recipe(RECIPE), source)
    assert mapping == {} and len(report['rows']) == 15
    assert report['cart_ready'] is False and report['order_submitted'] is False


def test_verified_whole_grain_and_exact_pack_rounding():
    source = {'schema_version': 1, 'supplier': 'test', 'products': {'CaraMunich II': {'packs': [
        {'pack_g': 100, 'sku': 'small', 'verified': True, 'whole_grain': False},
        {'pack_g': 500, 'sku': 'whole', 'verified': True, 'whole_grain': True},
        {'pack_g': 1000, 'sku': 'large', 'verified': True, 'whole_grain': True}]}}}
    mapping, report = resolve_catalog(load_recipe(RECIPE), source)
    assert mapping['CaraMunich II'] == {'pack_g': 500, 'sku': 'whole'}
    row = next(r for r in report['rows'] if r['ingredient'] == 'CaraMunich II')
    assert row['quantity'] == 1 and row['surplus_g'] == 50
    assert row['status'] == 'REVIEW'


def test_unverified_and_missing_id_never_generate_cart():
    source = {'schema_version': 1, 'supplier': 'test', 'products': {'Pale Ale Malt': {'packs': [
        {'pack_g': 1000, 'sku': 'unknown', 'verified': False, 'whole_grain': True}]}}}
    mapping, report = resolve_catalog(load_recipe(RECIPE), source)
    assert mapping == {} and report['cart_ready'] is False
    assert build_shopware_cart_preview(build_request(load_recipe(RECIPE), catalog=mapping))['request'] is None


def test_verified_pack_is_compatible_with_existing_rfq():
    source = {'schema_version': 1, 'supplier': 'test', 'products': {'Fermentis SafAle S-04': {'packs': [
        {'pack_g': 11.5, 'sku': 's04', 'verified': True, 'availability': 'confirmed',
         'shopware_product_id': 'f' * 32}]}}}
    mapping, report = resolve_catalog(load_recipe(RECIPE), source)
    row = next(x for x in build_request(load_recipe(RECIPE), catalog=mapping)['items'] if x['category'] == 'yeast')
    assert row['purchase_quantity'] == 1 and row['shopware_product_id'] == 'f' * 32
    assert report['cart_ready'] is False  # All 15 items must map


def test_bad_pack_and_unknown_name_rejected():
    recipe = load_recipe(RECIPE)
    for products in ({'unknown ingredient': {'packs': []}},
                     {'CaraMunich II': {'packs': [{'pack_g': 0, 'verified': True}]}},
                     {'CaraMunich II': {'packs': [{'pack_g': 100, 'verified': True, 'shopware_product_id': 'FAKE'}]}}):
        with pytest.raises(ValueError):
            resolve_catalog(recipe, {'schema_version': 1, 'supplier': 'test', 'products': products})


def test_cli_outputs_and_refuses_overwrite(tmp_path):
    prefix = tmp_path / 'shopping'
    source = ROOT / 'catalogs/braupartner.example.yaml'
    assert main([str(RECIPE), '--source', str(source), '--output-prefix', str(prefix)]) == 0
    assert yaml.safe_load((tmp_path / 'shopping.catalog.yaml').read_text(encoding='utf-8')) == {}
    assert json.loads((tmp_path / 'shopping.catalog-report.json').read_text(encoding='utf-8'))['cart_ready'] is False
    assert main([str(RECIPE), '--source', str(source), '--output-prefix', str(prefix)]) == 1
