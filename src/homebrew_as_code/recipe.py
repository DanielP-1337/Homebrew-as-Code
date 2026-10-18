"""Read and validate repository-owned brewing recipes."""

from pathlib import Path
from typing import Any

import yaml


class RecipeError(ValueError):
    """Invalid recipe content."""


def _positive_number(value: Any, field: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecipeError(f"{field} must be numeric")
    if value < 0 or (value == 0 and not allow_zero):
        raise RecipeError(f"{field} must be {'nonnegative' if allow_zero else 'positive'}")
    return float(value)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RecipeError(f"{field} must be a mapping")
    return value


def load_recipe(path: str | Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise RecipeError(f"Cannot read recipe: {exc}") from exc
    validate_recipe(data)
    return data


def validate_recipe(data: Any) -> None:
    root = _mapping(data, "recipe file")
    if root.get("schema_version") != 1:
        raise RecipeError("schema_version must be 1")
    identity = _mapping(root.get("recipe"), "recipe")
    for key in ("id", "name", "version"):
        if not isinstance(identity.get(key), str) or not identity[key].strip():
            raise RecipeError(f"recipe.{key} must be nonempty text")
    targets = _mapping(root.get("targets"), "targets")
    for key in ("packaged_volume_l", "original_gravity_plato", "alcohol_abv_percent", "bitterness_ibu"):
        _positive_number(targets.get(key), f"targets.{key}")
    mash = _mapping(root.get("mash"), "mash")
    _positive_number(mash.get("mash_in_temperature_c"), "mash.mash_in_temperature_c")
    steps = mash.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 10:
        raise RecipeError("mash.steps must contain 1 to 10 steps")
    for index, step in enumerate(steps):
        item = _mapping(step, f"mash.steps[{index}]")
        temp = _positive_number(item.get("temperature_c"), f"mash.steps[{index}].temperature_c")
        if temp > 100:
            raise RecipeError("Mash temperatures must not exceed 100 C")
        _positive_number(item.get("duration_min"), f"mash.steps[{index}].duration_min")
    boil = _mapping(root.get("boil"), "boil")
    duration = _positive_number(boil.get("duration_min"), "boil.duration_min")
    for index, addition in enumerate(boil.get("additions", [])):
        item = _mapping(addition, f"boil.additions[{index}]")
        remaining = _positive_number(item.get("remaining_min"), "addition.remaining_min", allow_zero=True)
        if remaining > duration:
            raise RecipeError("Boil addition is scheduled before boiling begins")
        if not isinstance(item.get("ingredient"), str) or not item["ingredient"].strip():
            raise RecipeError("Boil addition ingredient must be nonempty text")
    grains = root.get("fermentables")
    if not isinstance(grains, list) or not grains:
        raise RecipeError("fermentables must be a nonempty list")
    for index, grain in enumerate(grains):
        item = _mapping(grain, f"fermentables[{index}]")
        if not isinstance(item.get("name"), str) or not item["name"].strip():
            raise RecipeError("Each fermentable needs a name")
        _positive_number(item.get("amount_g"), "fermentable.amount_g")
        if item.get("purchase_form") != "whole":
            raise RecipeError("Fermentables must be purchased whole (uncrushed)")
    water = _mapping(root.get("water"), "water")
    volume = _positive_number(water.get("total_l"), "water.total_l")
    mash_volume = _positive_number(water.get("mash_l"), "water.mash_l")
    sparge_volume = _positive_number(water.get("sparge_l"), "water.sparge_l", allow_zero=True)
    if abs((mash_volume + sparge_volume) - volume) > 1e-6:
        raise RecipeError("Mash and sparge water must sum to total_l")
    salts = _mapping(water.get("salts_g"), "water.salts_g")
    for salt in ("calcium_chloride_dihydrate", "calcium_sulfate_dihydrate"):
        _positive_number(salts.get(salt), f"water.salts_g.{salt}", allow_zero=True)
    packaging = _mapping(root.get("packaging"), "packaging")
    if packaging.get("type") != "keg":
        raise RecipeError("Initial recipe requires keg packaging")
