"""Conservative catalog resolution without any network access."""
from copy import deepcopy
from pathlib import Path
import pytest
from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.myspeidel_catalog_resolver import api_get_inventory, resolve_snapshot
from homebrew_as_code.myspeidel_catalog_resolver_cli import main

RECIPE = Path(__file__).resolve().parents[1] / "recipes/lebkuchen-zauber/recipe.yaml"
SPEC = {"openapi":"3.0.3", "paths": {"/v1.0/propfind/malt": {"get": {"operationId":"listMalts"}},
                                           "/v1.0/hop": {"post": {}},
                                           "/v1.0/recipe": {"post": {}}}}
UID = "123e4567-e89b-42d3-a456-426614174000"


def entry(**kwargs):
    return {"kind":"malt", "name":"Pale Ale Malt", "uuid":UID,
            "source_get_path":"/v1.0/propfind/malt", "confirmed":True, **kwargs}


def test_endpoint_inventory_only_get():
    assert [x["path"] for x in api_get_inventory(SPEC)] == ["/v1.0/propfind/malt"]
    assert api_get_inventory(SPEC)[0]["authorized_for_client"] is False


def test_empty_snapshot_no_uuid_or_upload():
    report = resolve_snapshot(load_recipe(RECIPE), SPEC, {"schema_version":1,"entries":[]})
    assert report["upload_ready"] is False and report["api_payload"] is None
    assert report["resolved_count"] == 0 and report["recipe_count"] == 12


def test_exact_confirmed_and_casefold():
    report = resolve_snapshot(load_recipe(RECIPE), SPEC, {"schema_version":1,"entries":[entry()]})
    assert report["resolved_count"] == 1
    assert report["rows"][0]["catalog_uuid"] == UID


def test_unconfirmed_does_not_emit_uuid():
    x = entry(); x["confirmed"] = False
    report = resolve_snapshot(load_recipe(RECIPE), SPEC, {"schema_version":1,"entries":[x]})
    assert report["rows"][0]["catalog_uuid"] is None


def test_duplicate_ambiguous_blocked():
    report = resolve_snapshot(load_recipe(RECIPE), SPEC, {"schema_version":1,"entries":[entry(), entry()]})
    assert report["rows"][0]["status"] == "AMBIGUOUS"


def test_undocumented_endpoint_or_wrong_uuid_rejected():
    for field, value in (("source_get_path", "/v1.0/fake"), ("uuid", "fake")):
        x = entry();x[field] = value
        with pytest.raises(ValueError):
            resolve_snapshot(load_recipe(RECIPE), SPEC, {"schema_version":1,"entries":[x]})


def test_cli_writes_only_private_and_no_overwrite(tmp_path):
    import json, yaml
    spec_path = tmp_path / "spec.json"; spec_path.write_text(json.dumps(SPEC), encoding="utf-8")
    snapshot_path = tmp_path / "snapshot.yaml"; snapshot_path.write_text("schema_version: 1\nentries: []\n", encoding="utf-8")
    target = tmp_path / ".local" / "report.json"
    assert main([str(RECIPE), "--spec", str(spec_path), "--snapshot", str(snapshot_path), "--output", str(target)]) == 0
    assert main([str(RECIPE), "--spec", str(spec_path), "--snapshot", str(snapshot_path), "--output", str(target)]) == 1
    assert main([str(RECIPE), "--spec", str(spec_path), "--snapshot", str(snapshot_path), "--output", str(tmp_path / "public.json")]) == 1
