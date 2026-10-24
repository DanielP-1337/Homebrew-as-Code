"""Synthetic OpenAPI test fixture only; no vendor spec or private recipe data."""
import json
from copy import deepcopy
from pathlib import Path

from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.myspeidel_recipe_v5_draft import build_candidate, inspect_candidate, _check
from homebrew_as_code.myspeidel_recipe_v5_draft_cli import main

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes/lebkuchen-zauber/recipe.yaml"


def spec():
    recipe_ref = {"$ref": "#/components/schemas/recipe_v5"}
    return {
        "openapi": "3.0.3",
        "paths": {
            "/v1.0/recipe": {"post": {"requestBody": {"content": {"application/json": {"schema": recipe_ref}}}}},
            "/v1.0/recipe/{uuid}": {"get": {"responses": {"200": {"content": {"application/json": {"schema": recipe_ref}}}}}},
        },
        "components": {
            "schemas": {
                "recipe_v5": {
                    "type": "object", "additionalProperties": False,
                    "required": ["name", "bitterness", "mashing", "references"],
                    "properties": {
                        "name": {"type": "string"}, "bitterness": {"type": "number"},
                        "mashing": {"$ref": "#/components/schemas/mashing"},
                        "references": {"type": "object"},
                    },
                },
                "mashing": {"type": "object", "required": ["steps"], "properties": {"steps": {"type": "array", "items": {"type": "number"}}}},
            },
            "examples": {"recipe": {"value": {"name": "vendor example", "bitterness": 20, "mashing": {}, "references": {}}}},
        },
    }


def test_partial_candidate_keeps_vendor_fields_out_of_domain():
    candidate = build_candidate(load_recipe(RECIPE))
    assert candidate == {"name": "Lebkuchen-Zauber 2026", "bitterness": 21.0}
    assert "uuid" not in candidate and "owner" not in candidate


def test_report_explicitly_blocks_write_and_lists_required():
    draft, report = inspect_candidate(spec(), load_recipe(RECIPE))
    assert draft["name"].startswith("Lebkuchen")
    assert report["upload_ready"] is False and report["api_payload"] is None
    assert report["missing_required_paths"] == ["$.mashing", "$.references"]
    assert report["openapi_full_validation"] is False


def test_schema_recursive_required_and_array_type():
    issues = []
    _check({"mashing": {"steps": [1, "bad"]}}, {"type": "object", "required": ["mashing"],
        "properties": {"mashing": {"$ref": "#/components/schemas/mashing"}}}, spec(), "$", issues)
    assert {"path": "$.mashing.steps[1]", "code": "TYPE_MISMATCH"} in issues


def test_reject_additional_property():
    issues = []
    _check({"unexpected": True}, {"type": "object", "additionalProperties": False, "properties": {}}, spec(), "$", issues)
    assert issues == [{"path": "$.unexpected", "code": "ADDITIONAL_PROPERTY"}]


def test_no_vendor_example_leaks_to_report():
    _, report = inspect_candidate(spec(), load_recipe(RECIPE))
    assert "vendor example" not in json.dumps(report)


def test_cli_writes_two_files_and_blocks_overwrite(tmp_path):
    specfile = tmp_path / "openapi.json"
    specfile.write_text(json.dumps(spec()), encoding="utf-8")
    prefix = tmp_path / "recipe-v5"
    args = [str(RECIPE), "--spec", str(specfile), "--output-prefix", str(prefix)]
    assert main(args) == 0
    assert (tmp_path / "recipe-v5.candidate.json").exists()
    assert json.loads((tmp_path / "recipe-v5.report.json").read_text())["upload_ready"] is False
    assert main(args) == 1
