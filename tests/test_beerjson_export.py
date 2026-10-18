"""BeerJSON draft must preserve known facts without inventing mandatory data."""
import json
from pathlib import Path

from homebrew_as_code.beerjson_export import build_beerjson_draft_file
from homebrew_as_code.beerjson_cli import main

RECIPE = "recipes/lebkuchen-zauber/recipe.yaml"


def test_draft_preserves_ingredients_and_times():
    doc, report = build_beerjson_draft_file(RECIPE)
    recipe = doc["beerjson"]["recipes"][0]
    assert doc["beerjson"]["version"] == 3
    assert len(recipe["ingredients"]["fermentable_additions"]) == 6  # five grains and honey
    assert len(recipe["ingredients"]["hop_additions"]) == 1
    assert len(recipe["ingredients"]["miscellaneous_additions"]) == 5
    assert recipe["ingredients"]["hop_additions"][0]["timing"]["duration"]["value"] == 60
    assert [x["timing"]["duration"]["value"] for x in recipe["ingredients"]["miscellaneous_additions"]] == [5] * 5
    assert recipe["boil"]["boil_time"]["value"] == 60
    assert report["schema_valid"] is False


def test_does_not_fabricate_unmeasured_values():
    recipe = build_beerjson_draft_file(RECIPE)[0]["beerjson"]["recipes"][0]
    assert "efficiency" not in recipe and "batch_size" not in recipe and "author" not in recipe
    assert "mash" not in recipe
    assert all("color" not in x and "yield" not in x for x in recipe["ingredients"]["fermentable_additions"])


def test_cli_writes_separate_report(tmp_path):
    path = tmp_path / "test.beerjson"
    assert main([RECIPE, "--output", str(path)]) == 0
    assert json.loads(path.read_text(encoding="utf-8"))["beerjson"]["version"] == 3
    assert json.loads(path.with_suffix('.report.json').read_text(encoding="utf-8"))["import_ready"] is False


def test_cli_refuses_overwrite(tmp_path):
    path = tmp_path / "test.beerjson"
    assert main([RECIPE, "--output", str(path)]) == 0
    assert main([RECIPE, "--output", str(path)]) == 1


def test_cli_rejects_invalid_extension(tmp_path):
    assert main([RECIPE, "--output", str(tmp_path / "recipe.xml")]) == 1
    assert not (tmp_path / "recipe.xml").exists()
