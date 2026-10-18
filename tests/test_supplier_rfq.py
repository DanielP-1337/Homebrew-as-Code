"""Complete RFQ export uses evidence without pretending to place an order."""
import csv
import io
import json
from pathlib import Path

import pytest
import yaml

from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.supplier_rfq import build_rfq, render_rfq, _safe_csv, _safe_markdown
from homebrew_as_code.supplier_rfq_cli import main

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes/lebkuchen-zauber/recipe.yaml'
CATALOG = ROOT / 'catalogs/braupartner.verified.yaml'


def get_data():
    return load_recipe(RECIPE), yaml.safe_load(CATALOG.read_text(encoding='utf-8'))


def test_all_fifteen_and_eight_unresolved_retained():
    doc, report = build_rfq(*get_data())
    assert len(doc['positions']) == 15
    assert report['documented_offer_count'] == 7
    assert report['unresolved_count'] == 8
    assert report['ready_to_send_as_rfq'] is True
    assert report['ready_to_order'] is False and doc['order_submitted'] is False
    assert all(p['source_url'] for p in doc['positions'] if p['offer_type'] != 'UNRESOLVED')


def test_variable_weights_are_not_fixed_packs():
    doc, report = build_rfq(*get_data())
    rows = {r['ingredient']:r for r in doc['positions']}
    assert rows['Pale Ale Malt']['requested_g'] == 3000
    assert rows['CaraMunich II']['requested_g'] == 1000
    assert rows['CaraMunich II']['pack_count'] is None
    assert report['variable_weight_count'] == 4
    assert rows['Chocolate Malt']['pack_count'] == 1


def test_csv_markdown_json_consistent():
    rendered = render_rfq(*get_data())
    doc = json.loads(rendered['.rfq.json'])
    csvrows = list(csv.DictReader(io.StringIO(rendered['.rfq.csv']), delimiter=';'))
    assert len(csvrows) == len(doc['positions']) == 15
    assert 'variable Gewichtsmenge (keine Packung)' in rendered['.rfq.md']
    assert 'Mild honey' in rendered['.rfq.md']
    assert 'shopware_product_id' not in rendered['.rfq.json']


def test_safe_text_output():
    assert _safe_csv('  =HYPERLINK(1)') == "'  =HYPERLINK(1)"
    assert '<script>' not in _safe_markdown('<script>|hello\nworld')
    assert '&#124;' in _safe_markdown('<script>|hello\nworld')


def test_cli_creates_all_four_and_refuses_overwrite(tmp_path):
    pre = tmp_path / 'request'
    argv = [str(RECIPE), '--catalog', str(CATALOG), '--output-prefix', str(pre)]
    assert main(argv) == 0
    assert all(Path(str(pre)+ext).exists() for ext in ('.rfq.json','.rfq.csv','.rfq.md','.rfq-report.json'))
    assert main(argv) == 1


def test_bad_catalog_does_not_create_files(tmp_path):
    pre = tmp_path / 'bad'
    cat = tmp_path / 'catalog.yaml'
    cat.write_text('schema_version: 1\nsupplier: wrong\n', encoding='utf-8')
    assert main([str(RECIPE), '--catalog', str(cat), '--output-prefix', str(pre)]) == 1
    assert not list(tmp_path.glob('bad.*'))
