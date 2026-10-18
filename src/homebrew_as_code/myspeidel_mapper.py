"""Offline-only mapping of confirmed Braumeister program fields.

This is intentionally NOT a MySpeidel recipe_v5 upload document.
Ingredients, step semantics and UUID references require separate verification.
"""
from __future__ import annotations

from typing import Any

from .recipe import load_recipe, validate_recipe


class MappingError(ValueError):
    """A recipe cannot be represented by the currently confirmed subset."""


def map_program(recipe: dict[str, Any]) -> dict[str, Any]:
    """Produce a deterministic, explicitly incomplete program fragment.

    No network access, identifiers, ingredient guesses or API writes.
    """
    validate_recipe(recipe)
    mash = recipe["mash"]
    boil = recipe["boil"]
    water = recipe["water"]
    if len(mash["steps"]) > 10:
        raise MappingError("Too many mash rests")
    if abs(float(boil.get("temperature_c", 100)) - 100) > 0.01:
        # Do not silently change a controller temperature.
        raise MappingError("This mapper only supports 100 C boil recipes")
    return {
        "format": "homebrew-as-code/myspeidel-program-fragment-v1",
        "upload_ready": False,
        "machine_size_l": 20,
        "mapped": {
            "mashing": {
                "temperature": mash["mash_in_temperature_c"],
                "adds": {"water": {"water_amount_start": water["mash_l"]}},
            },
            "rest": {
                "steps": [
                    {"temperature": step["temperature_c"], "duration": step["duration_min"]}
                    for step in mash["steps"]
                ],
                "water_amount_addition": water["sparge_l"],
            },
            "boil": {
                "boiling_temperature": boil.get("temperature_c", 100),
                "boiling_duration": boil["duration_min"],
            },
        },
        "not_mapped": [
            "boil.steps: duration semantics and ingredient UUIDs not verified",
            "mashing.adds.malts: catalog UUIDs and amount units not verified",
            "mashing.adds.water.uuid: water-type UUID not resolved",
            "fermentation, maturation and other recipe_v5 required fields not mapped",
            "RO water salts, spice-contact time and keg settings are local-only",
        ],
    }


def map_program_file(path: str) -> dict[str, Any]:
    return map_program(load_recipe(path))
