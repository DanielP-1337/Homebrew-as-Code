"""Offline, deliberately incomplete BeerJSON schema-3 recipe export.

The legacy draft lacks mandatory exchange data; it has no pinned schema contract.
Do NOT call this file schema-valid or import-ready before filling these gaps.
"""
from __future__ import annotations

from typing import Any

from .recipe import load_recipe, validate_recipe


def _qty(unit: str, value: float) -> dict[str, Any]:
    return {"unit": unit, "value": float(value)}


def build_beerjson_draft(recipe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a BeerJSON-shaped draft and a separate loss/validation report.

    No schema-required efficiency, malt color/yield, grain temperature, or
    fermenter batch size is fabricated. No network calls are made.
    """
    validate_recipe(recipe)
    boil_duration = recipe["boil"]["duration_min"]
    ingredients: dict[str, Any] = {"fermentable_additions": [], "hop_additions": [], "miscellaneous_additions": []}
    for grain in recipe["fermentables"]:
        ingredients["fermentable_additions"].append({
            "name": grain["name"], "type": "grain", "amount": _qty("kg", grain["amount_g"] / 1000)
        })
    for addition in recipe["boil"].get("additions", []):
        remaining = float(addition["remaining_min"])
        if remaining != int(remaining):
            raise ValueError("BeerJSON TimeType requires integer minutes")
        timing = {"use": "add_to_boil", "duration": {"unit": "min", "value": int(remaining)}}
        common = {"name": addition["ingredient"], "amount": _qty("g", addition["amount_g"]), "timing": timing}
        if "alpha_acid_percent" in addition:
            ingredients["hop_additions"].append({**common, "alpha_acid": _qty("%", addition["alpha_acid_percent"])})
        else:
            kind = "spice" if remaining == 5 else "other"
            if "honey" in addition["ingredient"].casefold():
                # Honey contributes fermentable extract; BeerJSON requires color and yield
                # for this category. Carry it in fermentables; never label it a spice.
                ingredients["fermentable_additions"].append({
                    **common, "type": "honey",
                })
            else:
                ingredients["miscellaneous_additions"].append({**common, "type": kind})
    document = {"beerjson": {"version": 3, "recipes": [{
        "name": recipe["recipe"]["name"], "type": "all grain",
        "ingredients": ingredients,
        "original_gravity": _qty("plato", recipe["targets"]["original_gravity_plato"]),
        "alcohol_by_volume": _qty("%", recipe["targets"]["alcohol_abv_percent"]),
        "carbonation": float(recipe["packaging"]["carbonation_volumes"]),
        "boil": {"boil_time": {"unit": "min", "value": int(boil_duration)}},
    }]}}
    missing = [
        "recipes[0].author: not supplied in source YAML",
        "recipes[0].efficiency.brewhouse: unmeasured",
        "recipes[0].batch_size: fermenter volume unknown (packaged volume is not equivalent)",
        "recipes[0].ingredients.fermentable_additions[*].yield: not supplied",
        "recipes[0].ingredients.fermentable_additions[*].color: not supplied",
        "recipes[0].mash: omitted; grain_temperature unknown (mash rest data retained in YAML)",
        "recipes[0].fermentation: omitted; source has temperature range but no phase schedule",
        "water chemistry/salt additions: omitted pending verified export mapping",
        "flameout spice contact: not modeled as separate process step",
        "IBU method: unknown; target IBU omitted instead of guessing method",
    ]
    report = {
        "format": "homebrew-as-code/beerjson-export-report-v1",
        "schema_target": "legacy unvalidated draft (declared version 3; no pinned schema)",
        "schema_valid": False,
        "import_ready": False,
        "myspeidel_import_ready": False,
        "missing_or_unmapped": missing,
        "notes": "BeerJSON is not BeerXML; MySpeidel screenshot advertises BeerXML and .recipe import only.",
    }
    return document, report


def build_beerjson_draft_file(path: str) -> tuple[dict[str, Any], dict[str, Any]]:
    return build_beerjson_draft(load_recipe(path))
