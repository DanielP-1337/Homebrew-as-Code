"""Synthetic schema fixture: never reproduce a vendor example in the repo."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from homebrew_as_code.myspeidel_openapi_reference import inspect_spec, inspect_files
from homebrew_as_code.myspeidel_openapi_reference_cli import main
from homebrew_as_code.recipe import load_recipe

RECIPE = Path(__file__).resolve().parents[1] / "recipes/lebkuchen-zauber/recipe.yaml"


def fixture():
    return {
        "openapi": "3.0.3",
        "components": {
            "schemas": {"recipe_v5": {"type": "object", "required": ["name", "machine_type", "uuid"],
                                      "properties": {"name": {"type": "string"}, "machine_type": {"type": "object"},
                                                     "uuid": {"type": "string"}, "boil": {"type": "object"}}}},
            "examples": {"recipe": {"value": {"name": "Synthetic fixture", "machine_type": {}, "uuid": "TEST"}}},
        },
        "paths": {
            "/v1.0/recipe": {"post": {"requestBody": {"content": {"application/json": {
                "schema": {"oneOf": [{"$ref": "#/components/schemas/recipe_v5"}]}}}},
                "parameters": [{"name": "dryRun", "in": "query"}]}},
            "/v1.0/recipe/{uuid}": {"get": {"responses": {"200": {"content": {"application/json": {
                "schema": {"$ref": "#/components/schemas/recipe_v5"}}}}}}},
        },
    }


def test_inventory_does_not_claim_verified_mapping():
    report = inspect_spec(fixture(), load_recipe(RECIPE))
    assert report["post_supports_recipe_v5"] is True
    assert "dryRun" in report["post_parameter_names"]
    assert len(report["api_required_fields"]) == 3
    assert report["upload_ready"] is False and report["api_payload"] is None
    assert all(x["mapping_verified"] is False for x in report["fields"])
    assert next(x for x in report["fields"] if x["api_field"] == "uuid")["status"] == "UNMAPPED_OR_UNKNOWN"
    assert "Synthetic fixture" not in json.dumps(report)


def test_missing_example_required_is_detected():
    spec = fixture()
    del spec["components"]["examples"]["recipe"]["value"]["uuid"]
    assert inspect_spec(spec, load_recipe(RECIPE))["example_missing_required"] == ["uuid"]


def test_missing_api_ref_fails_closed():
    spec = fixture()
    spec["paths"]["/v1.0/recipe"]["post"]["requestBody"]["content"]["application/json"]["schema"] = {}
    with pytest.raises(ValueError, match="advertise recipe_v5"):
        inspect_spec(spec, load_recipe(RECIPE))


def test_missing_example_fails_closed():
    spec = fixture()
    spec["components"]["examples"]["recipe"] = {}
    with pytest.raises(ValueError, match="example"):
        inspect_spec(spec, load_recipe(RECIPE))


def test_cli_offline_file_and_no_overwrite(tmp_path):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(fixture()), encoding="utf-8")
    out = tmp_path / "report.json"
    assert main([str(RECIPE), "--spec", str(spec), "--output", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["source_sha256"]) == 64
    assert data["api_payload"] is None
    assert main([str(RECIPE), "--spec", str(spec), "--output", str(out)]) == 1


def test_reject_non_openapi():
    spec = fixture()
    spec["openapi"] = "2.0"
    with pytest.raises(ValueError, match="OpenAPI 3"):
        inspect_spec(spec, load_recipe(RECIPE))
