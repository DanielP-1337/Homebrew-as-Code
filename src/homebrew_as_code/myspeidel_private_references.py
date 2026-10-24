"""Extract references from one user-selected private MySpeidel recipe.

All observations are UNCONFIRMED until a human checks the website. Never writes
cloud data, names or raw recipes. Only identifiers observed in documented GET.
"""
from __future__ import annotations

from typing import Any
from .myspeidel import UUID_PATTERN
from .myspeidel_catalog_resolver import _recipe_items


def _uuid(value: Any) -> bool:
    return isinstance(value, str) and UUID_PATTERN.fullmatch(value) is not None


def extract_observations(detail: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(detail, dict) or not isinstance(detail.get('machine_type'), dict) or detail['machine_type'].get('size') != 20:
        raise ValueError('Expected selected 20 L recipe detail')
    observations = []
    def collect(container: Any, field: str, category: str, path: str) -> None:
        if container is None:
            return
        if not isinstance(container, list):
            raise ValueError('Unexpected reference container type')
        for index, entry in enumerate(container):
            if not isinstance(entry, dict):
                raise ValueError('Unexpected reference entry type')
            value = entry.get(field)
            if not _uuid(value):
                raise ValueError('Missing/invalid catalog reference UUID')
            observations.append({'index': len(observations), 'container': f'{path}[{index}]',
                                 'api_field': field, 'observed_kind': category,
                                 'uuid': value.lower(), 'web_confirmed': False})
    mash = detail.get('mashing', {})
    if not isinstance(mash, dict):
        raise ValueError('mashing must be an object')
    adds = mash.get('adds', {})
    if not isinstance(adds, dict):
        raise ValueError('mashing.adds must be an object')
    collect(adds.get('malts', []), 'malt_uuid', 'malt', '$.mashing.adds.malts')
    boil = detail.get('boil', {})
    if not isinstance(boil, dict) or not isinstance(boil.get('steps'), list):
        raise ValueError('boil.steps missing')
    for step_idx, step in enumerate(boil['steps']):
        if not isinstance(step, dict) or not isinstance(step.get('adds', {}), dict):
            raise ValueError('boil step invalid')
        adds = step.get('adds', {})
        for field, key, kind in [('hops','hop_uuid','hop'), ('ingredients','ingredient_uuid','ingredient')]:
            collect(adds.get(field, []), key, kind, f'$.boil.steps[{step_idx}].adds.{field}')
    return {'format':'homebrew-as-code/myspeidel-private-observations-v1',
            'source':'selected_private_recipe_get', 'machine_size_l':20,
            'confirmed':False, 'upload_ready':False, 'observations':observations}


def confirm_observations(recipe: dict[str, Any], observed: dict[str, Any],
                         decisions: dict[str, Any]) -> dict[str, Any]:
    """One explicit verified name per unique observed UUID. No guessing or fuzzy matching."""
    if not isinstance(observed, dict) or observed.get('format') != 'homebrew-as-code/myspeidel-private-observations-v1' or observed.get('source') != 'selected_private_recipe_get':
        raise ValueError('Unknown observation format')
    rows = observed.get('observations')
    selections = decisions.get('confirmations') if isinstance(decisions, dict) else None
    if not isinstance(rows, list) or not isinstance(selections, list):
        raise ValueError('Observations and confirmations must be lists')
    expected = {(item['kind'], item['name'].casefold()) for item in _recipe_items(recipe)}
    seen_idx, seen_names = set(), set()
    result = []
    for selection in selections:
        if not isinstance(selection, dict) or selection.get('web_verified') is not True:
            raise ValueError('Each confirmation requires web_verified: true')
        idx, kind, name = (selection.get(x) for x in ('observation_index','kind','name'))
        if type(idx) is not int or not 0 <= idx < len(rows) or idx in seen_idx:
            raise ValueError('Invalid or duplicate observation index')
        if not isinstance(kind, str) or not isinstance(name, str) or (kind,name.casefold()) not in expected:
            raise ValueError('Confirmation must exactly match recipe ingredient kind and name')
        if (kind,name.casefold()) in seen_names:
            raise ValueError('Duplicate ingredient confirmation')
        observation = rows[idx]
        if not isinstance(observation, dict) or not _uuid(observation.get('uuid')):
            raise ValueError('Observation UUID is invalid')
        # Only known categories. A spice under adds.hops is permitted only when
        # individually human-confirmed; never automatically reclassified.
        if kind == 'malt' and observation.get('observed_kind') != 'malt':
            raise ValueError('Malt must come from malt reference container')
        if kind == 'hop' and observation.get('observed_kind') != 'hop':
            raise ValueError('Hop must come from hop reference container')
        if kind == 'ingredient' and observation.get('observed_kind') not in ('hop','ingredient'):
            raise ValueError('Ingredient must come from boil reference container')
        seen_idx.add(idx); seen_names.add((kind,name.casefold()))
        result.append({'kind':kind, 'name':name, 'uuid':observation['uuid'],
                       'source_get_path':'/v1.0/recipe/{uuid}',
                       'provenance':'manually_confirmed_private_recipe_get',
                       'observed_container':observation['container'],
                       'confirmed':True, 'web_verified':True})
    return {'schema_version':1, 'entries':result}
