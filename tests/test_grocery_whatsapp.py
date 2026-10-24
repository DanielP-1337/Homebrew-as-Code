"""Grocery WhatsApp content is human-readable and never sent automatically."""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from homebrew_as_code.grocery_whatsapp import render_whatsapp
from homebrew_as_code.grocery_whatsapp_cli import main
from homebrew_as_code.recipe import load_recipe

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes/lebkuchen-zauber/recipe.yaml'
CATALOG = ROOT / 'catalogs/braupartner.verified.yaml'


def render():
    return render_whatsapp(load_recipe(RECIPE), yaml.safe_load(CATALOG.read_text(encoding='utf-8')))


def test_only_six_grocery_lines():
    text = render()
    assert sum(line.startswith('☐ ') for line in text.splitlines()) == 6
    for name in ('Honig', 'Zimtstangen', 'Ingwer', 'Gewürznelken', 'Muskatnuss', 'Bio-Orange'):
        assert name in text
    for name in ('Goldings', 'SafAle', 'Calciumchlorid', 'Pale Ale Malt'):
        assert name not in text


def test_preserves_precise_recipe_doses_and_retail_advice():
    text = render()
    assert '250 g' in text and '5 g' in text and '12 g' in text
    assert '0,2 g' in text and '0,3 g' in text and '8 g' in text
    assert 'nicht gemahlen' in text and 'unbehandelte' in text.lower()


def test_rejects_unreviewed_recipe_ingredients():
    recipe = deepcopy(load_recipe(RECIPE))
    recipe['boil']['additions'].append({'ingredient': 'Vanilla beans', 'amount_g': 2, 'remaining_min': 5})
    source = yaml.safe_load(CATALOG.read_text(encoding='utf-8'))
    with pytest.raises(ValueError, match='Unclassified'):
        render_whatsapp(recipe, source)


def test_cli_creates_utf8_and_refuses_overwrite(tmp_path):
    out = tmp_path / 'grocery.whatsapp.txt'
    args = [str(RECIPE), '--catalog', str(CATALOG), '--output', str(out)]
    assert main(args) == 0
    assert '🛒' in out.read_text(encoding='utf-8')
    assert main(args) == 1


def test_cli_rejects_non_txt(tmp_path):
    out = tmp_path / 'message.json'
    assert main([str(RECIPE), '--catalog', str(CATALOG), '--output', str(out)]) == 1
    assert not out.exists()
