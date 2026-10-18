"""Offline ingredient plan; deliberately NOT a MySpeidel upload payload.

No ingredient catalog identifiers are guessed. Hop times remain in the
web-form convention (minutes before end), not API boil.step durations.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any

from .myspeidel_mapper import MappingError, map_program
from .recipe import load_recipe


def _number(value: Any, field: str, *, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise MappingError(f"{field} must be a finite number")
    if value < 0 or (not allow_zero and value == 0):
        raise MappingError(f"{field} must be positive" if not allow_zero else f"{field} must be nonnegative")
    return float(value)


def build_ingredient_plan(recipe: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, non-uploadable manifest and known program fields."""
    base = map_program(recipe)
    mash_start = _number(recipe['mash']['mash_in_temperature_c'], 'mash-in temperature')
    prev = mash_start
    for index, step in enumerate(recipe['mash']['steps']):
        temperature = _number(step['temperature_c'], f'rest {index} temperature')
        if temperature < prev:
            raise MappingError('Mash rest temperatures must be nondecreasing')
        prev = temperature
    duration = _number(recipe['boil']['duration_min'], 'boil duration')
    if duration > 180:
        raise MappingError('Boil duration exceeds frontend limit of 180 min')
    malts = []
    for index, item in enumerate(recipe['fermentables']):
        grams = _number(item['amount_g'], f'malt {index} amount')
        malts.append({'name': item['name'], 'amount_kg': round(grams / 1000, 6),
                      'catalog_uuid': None, 'resolution': 'REQUIRED'})
    schedule = defaultdict(lambda: {'hops': [], 'other_ingredients': []})
    for index, item in enumerate(recipe['boil'].get('additions', [])):
        remaining = _number(item['remaining_min'], f'addition {index} time', allow_zero=True)
        if remaining > duration:
            raise MappingError('Addition occurs before boil starts')
        amount = _number(item.get('amount_g'), f'addition {index} amount')
        if 'alpha_acid_percent' in item:
            acid = _number(item['alpha_acid_percent'], f'hop {index} acid', allow_zero=True)
            if acid > 100:
                raise MappingError('Hop alpha-acid percent exceeds 100')
            schedule[remaining]['hops'].append({
                'name': item['ingredient'], 'amount_g': amount,
                'alpha_acid_percent': acid, 'catalog_uuid': None,
                'resolution': 'REQUIRED',
            })
        else:
            schedule[remaining]['other_ingredients'].append({
                'name': item['ingredient'], 'amount_g': amount,
                'catalog_uuid': None, 'resolution': 'REQUIRED',
            })
    additions = [{'minutes_before_end': minutes, **schedule[minutes]}
                 for minutes in sorted(schedule, reverse=True)]
    return {
        'format': 'homebrew-as-code/myspeidel-ingredient-plan-v1',
        'upload_ready': False,
        'api_payload': None,
        'machine_size_l': base['machine_size_l'],
        'mapped_program': base['mapped'],
        'malts': malts,
        'boil_additions_web_form_timeline': additions,
        'blocked_by': [
            'Resolve every ingredient catalog UUID from authoritative MySpeidel catalog data',
            'Verify conversion from web-form minutes-before-end to API boil.steps durations',
            'Verify full recipe_v5 envelope, water UUID, fermentation/maturation and required fields',
            'No API writer exists; generated manifest must never be POSTed',
        ],
    }


def build_ingredient_plan_file(path: str) -> dict[str, Any]:
    return build_ingredient_plan(load_recipe(path))
