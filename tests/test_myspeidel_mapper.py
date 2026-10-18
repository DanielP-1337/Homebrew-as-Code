"""Offline tests for explicitly incomplete MySpeidel program fragments."""
import copy
import json

import pytest

from homebrew_as_code.myspeidel_mapper import MappingError, map_program, map_program_file
from homebrew_as_code.myspeidel_mapper_cli import main
from homebrew_as_code.recipe import load_recipe

RECIPE_PATH = "recipes/lebkuchen-zauber/recipe.yaml"


def test_lebkuchen_program_fields():
    result = map_program_file(RECIPE_PATH)
    assert result["upload_ready"] is False
    assert result["machine_size_l"] == 20
    assert result["mapped"]["mashing"]["temperature"] == 60
    assert result["mapped"]["rest"]["steps"] == [
        {"temperature": 63, "duration": 20},
        {"temperature": 72, "duration": 45},
        {"temperature": 78, "duration": 10},
    ]
    assert result["mapped"]["boil"] == {"boiling_temperature": 100, "boiling_duration": 60}
    assert result["mapped"]["mashing"]["adds"]["water"]["water_amount_start"] == 23
    assert result["mapped"]["rest"]["water_amount_addition"] == 5


def test_no_unverified_ingredient_payloads():
    result = map_program_file(RECIPE_PATH)
    program = result["mapped"]
    assert "steps" not in program["boil"]
    assert "malts" not in program["mashing"]["adds"]
    assert "uuid" not in program["mashing"]["adds"]["water"]
    assert len(result["not_mapped"]) >= 4


def test_deterministic_and_does_not_mutate_input():
    recipe = load_recipe(RECIPE_PATH)
    original = copy.deepcopy(recipe)
    assert map_program(recipe) == map_program(recipe)
    assert recipe == original


def test_rejects_nonstandard_boil_temperature():
    recipe = load_recipe(RECIPE_PATH)
    recipe["boil"]["temperature_c"] = 99
    with pytest.raises(MappingError, match="100 C"):
        map_program(recipe)


def test_rejects_invalid_recipe():
    recipe = load_recipe(RECIPE_PATH)
    recipe["water"]["sparge_l"] = -1
    with pytest.raises(ValueError):
        map_program(recipe)


def test_cli_has_no_authentication_or_network(monkeypatch, capsys):
    # Even an invalid token is irrelevant; no network client instantiated.
    monkeypatch.delenv("MYSPEIDEL_TOKEN", raising=False)
    assert main([RECIPE_PATH]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["upload_ready"] is False
    assert output["mapped"]["rest"]["steps"][1]["duration"] == 45


def test_cli_missing_recipe_fails(capsys):
    assert main(["missing-recipe-file.yaml"]) == 1
    assert "ERROR" in capsys.readouterr().err
