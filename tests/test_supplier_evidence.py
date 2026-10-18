from copy import deepcopy
from pathlib import Path
import pytest
import yaml
from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.supplier_evidence import audit_offers
from homebrew_as_code.supplier_evidence_cli import main
from homebrew_as_code.supplier_catalog import resolve_catalog

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes/lebkuchen-zauber/recipe.yaml'
CATALOG = ROOT / 'catalogs/braupartner.verified.yaml'


def inputs():
    return load_recipe(RECIPE), yaml.safe_load(CATALOG.read_text(encoding='utf-8'))


def test_exact_documented_skus_and_rounding():
    recipe, source = inputs()
    report = audit_offers(recipe, source)
    rows = {x['ingredient']: x for x in report['rows']}
    assert len(rows) == 15
    assert rows['Pale Ale Malt']['supplier_sku'] == '10-303A-UGS'
    assert rows['Pale Ale Malt']['requested_g'] == 3000
    assert rows['Munich Malt Type II']['requested_g'] == 1500
    assert rows['CaraMunich II']['requested_g'] == 1000  # merchant minimum, not a 500g pack
    assert rows['Melanoidin Malt']['requested_g'] == 1000
    assert rows['Chocolate Malt']['supplier_sku'] == '10-009A-KLU'
    assert rows['Chocolate Malt']['quantity'] == 1
    assert rows['Goldings pellets']['quantity'] == 1
    assert rows['Fermentis SafAle S-04']['quantity'] == 1
    assert report['cart_ready'] is False and report['order_submitted'] is False


def test_old_catalog_resolver_never_converts_variable_to_cart():
    recipe, source = inputs()
    mapping, report = resolve_catalog(recipe, source)
    assert set(mapping) == {'Chocolate Malt', 'Goldings pellets', 'Fermentis SafAle S-04'}
    assert report['cart_ready'] is False


def test_no_fake_ids_or_prices():
    _, source = inputs()
    for spec in source['products'].values():
        for p in spec.get('packs', []):
            assert 'shopware_product_id' not in p and 'price' not in p
        if 'offer' in spec:
            assert 'shopware_product_id' not in spec['offer'] and 'price' not in spec['offer']


def test_external_or_fake_evidence_rejected():
    recipe, source = inputs()
    bad = deepcopy(source)
    bad['products']['Pale Ale Malt']['offer']['source_url'] = 'https://braupartner.de.evil.test/fake'
    with pytest.raises(ValueError, match='source_url'):
        audit_offers(recipe, bad)
    bad = deepcopy(source)
    bad['products']['Pale Ale Malt']['offer']['min_g'] = 0
    with pytest.raises(ValueError, match='min_g'):
        audit_offers(recipe, bad)


def test_cli_output_and_overwrite(tmp_path):
    dest = tmp_path/'evidence.json'
    args = [str(RECIPE), '--catalog', str(CATALOG), '--output', str(dest)]
    assert main(args) == 0
    assert 'supplier-evidence-v1' in dest.read_text(encoding='utf-8')
    assert main(args) == 1
