"""Offline BeerXML export; tests do not access any MySpeidel account."""
from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ET

import pytest

from homebrew_as_code.beerxml_cli import main
from homebrew_as_code.beerxml_export import BeerXmlError, build_beerxml
from homebrew_as_code.recipe import load_recipe

RECIPE = "recipes/lebkuchen-zauber/recipe.yaml"


def params():
    # Test-only synthetic data. Never shipped as brewing advice.
    grains = load_recipe(RECIPE)["fermentables"]
    return {"brewer": "TEST", "batch_size_l": 21, "boil_size_l": 25,
            "efficiency_percent": 70,
            "malts": {g["name"]: {"yield_percent": 72, "color_srm": 4} for g in grains},
            "honey": {"yield_percent": 78, "color_srm": 2},
            "yeast": {"type": "Ale", "form": "Dry"}}


def test_draft_missing_inputs_is_not_import_ready():
    content, report = build_beerxml(load_recipe(RECIPE))
    root = ET.fromstring(content)
    assert root.tag == "RECIPES"
    assert root.findtext("RECIPE/BOIL_TIME") == "60.0"
    assert "BREWER" not in [x.tag for x in root.find("RECIPE")]
    assert report["import_candidate"] is False
    assert report["required_fields_supplied"] is False


def test_candidate_preserves_hop_and_spices():
    content, report = build_beerxml(load_recipe(RECIPE), params())
    root = ET.fromstring(content)
    r = root.find("RECIPE")
    assert report["import_candidate"] is True
    assert len(r.findall("FERMENTABLES/FERMENTABLE")) == 6
    assert len(r.findall("HOPS/HOP")) == 1
    assert len(r.findall("MISCS/MISC")) == 5
    assert r.findtext("HOPS/HOP/TIME") == "60.0"
    assert r.findtext("HOPS/HOP/AMOUNT") == "0.06"
    assert all(x.findtext("TIME") == "5.0" for x in r.findall("MISCS/MISC"))
    assert r.findtext("YEASTS/YEAST/AMOUNT") == "0.0115"
    assert r.findtext("MASH/MASH_STEPS/MASH_STEP/STEP_TEMP") == "63"
    assert report["myspeidel_import_verified"] is False
    assert report["manual_review_required"] is True
    assert any("honey exact" in x for x in report["missing_or_lossy"])


def test_does_not_modify_recipe():
    recipe = load_recipe(RECIPE)
    orig = copy.deepcopy(recipe)
    assert build_beerxml(recipe, params()) == build_beerxml(recipe, params())
    assert recipe == orig


def test_invalid_values_rejected():
    p = params()
    p["efficiency_percent"] = float("nan")
    with pytest.raises(BeerXmlError):
        build_beerxml(load_recipe(RECIPE), p)
    p = params()
    p["malts"]["Chocolate Malt"]["color_srm"] = -1
    with pytest.raises(BeerXmlError):
        build_beerxml(load_recipe(RECIPE), p)


def test_xml_escaping():
    recipe = load_recipe(RECIPE)
    recipe["recipe"]["name"] = "Brew & <test>"
    xml, _ = build_beerxml(recipe, params())
    assert ET.fromstring(xml).findtext("RECIPE/NAME") == "Brew & <test>"


def test_cli_draft_and_no_overwrite(tmp_path, capsys):
    target = tmp_path / "test.xml"
    assert main([RECIPE, "--output", str(target)]) == 0
    assert "INCOMPLETE DRAFT" in capsys.readouterr().out
    report = json.loads(target.with_suffix(".report.json").read_text())
    assert report["import_candidate"] is False
    original = target.read_bytes()
    assert main([RECIPE, "--output", str(target)]) == 1
    assert target.read_bytes() == original


def test_cli_parameters(tmp_path):
    import yaml
    cfg = tmp_path / "params.yml"
    cfg.write_text(yaml.safe_dump(params()), encoding="utf-8")
    target = tmp_path / "candidate.xml"
    assert main([RECIPE, "--parameters", str(cfg), "--output", str(target)]) == 0
    assert json.loads(target.with_suffix(".report.json").read_text())["import_candidate"] is True


def test_cli_invalid_extension(tmp_path):
    assert main([RECIPE, "--output", str(tmp_path / "test.recipe")]) == 1
