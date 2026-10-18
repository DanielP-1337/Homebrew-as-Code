from copy import deepcopy
from pathlib import Path

import pytest

from homebrew_as_code.recipe import RecipeError, load_recipe, validate_recipe

RECIPE = Path(__file__).resolve().parents[1] / "recipes/lebkuchen-zauber/recipe.yaml"


def test_recipe_passes_validation():
    recipe = load_recipe(RECIPE)
    assert sum(item["amount_g"] for item in recipe["fermentables"]) == 5100
    assert recipe["packaging"]["type"] == "keg"
    assert len(recipe["mash"]["steps"]) == 3


def test_rejects_incorrect_water_balance():
    recipe = deepcopy(load_recipe(RECIPE))
    recipe["water"]["sparge_l"] = 7.0
    with pytest.raises(RecipeError, match="sum to total"):
        validate_recipe(recipe)


def test_rejects_crushed_malt():
    recipe = deepcopy(load_recipe(RECIPE))
    recipe["fermentables"][0]["purchase_form"] = "crushed"
    with pytest.raises(RecipeError, match="whole"):
        validate_recipe(recipe)


def test_rejects_overscheduled_hop_addition():
    recipe = deepcopy(load_recipe(RECIPE))
    recipe["boil"]["additions"][0]["remaining_min"] = 61
    with pytest.raises(RecipeError, match="before boiling"):
        validate_recipe(recipe)
