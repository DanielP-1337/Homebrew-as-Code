"""Load an offline brew plan linking independent recipe and equipment domains.

No vendor SDK, network requests, automatic scaling, or device operations.
"""
from __future__ import annotations

from pathlib import Path
import math
import yaml

from .recipe import load_recipe


class BrewPlanError(ValueError):
    """Invalid equipment definition or brew-plan reference."""


def _document(path: Path):
    try:
        value = yaml.safe_load(path.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        raise BrewPlanError(f'Cannot load YAML: {path.name}') from exc
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise BrewPlanError('Expected YAML mapping with schema_version 1')
    return value


def _number(value, label, *, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BrewPlanError(f'{label} must be finite numeric')
    if value < 0 or (value == 0 and not allow_zero):
        raise BrewPlanError(f'{label} must be positive')
    return float(value)


def _required_text(node, field):
    value = node.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BrewPlanError(f'Missing {field}')
    return value


def load_equipment(path: str | Path):
    data = _document(Path(path))
    equipment = data.get('equipment')
    params = data.get('parameters')
    source = data.get('reference')
    if not isinstance(equipment, dict) or not isinstance(params, dict) or not isinstance(source, dict):
        raise BrewPlanError('Missing equipment, reference or parameters')
    for field in ('id', 'manufacturer', 'model'):
        _required_text(equipment, field)
    for field in ('provider', 'profile_name', 'evidence', 'verification'):
        _required_text(source, field)
    for field in ('batch_volume_l', 'pre_boil_volume_l', 'boil_duration_min',
                  'brewhouse_efficiency_percent', 'trub_chiller_loss_l',
                  'hop_utilization_percent'):
        _number(params.get(field), field)
    _number(params.get('lauter_deadspace_l'), 'lauter_deadspace_l', allow_zero=True)
    if params['pre_boil_volume_l'] <= params['batch_volume_l']:
        raise BrewPlanError('Pre-boil volume must exceed batch volume')
    if params['brewhouse_efficiency_percent'] > 100 or params['hop_utilization_percent'] > 200:
        raise BrewPlanError('Implausible profile percentage')
    return data


def _repo_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise BrewPlanError('Expected repository-relative POSIX path')
    path = Path(relative)
    if path.is_absolute() or any(p in ('.', '..') for p in path.parts):
        raise BrewPlanError('Unsafe reference path')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise BrewPlanError('Reference escapes repository')
    if not resolved.is_file():
        raise BrewPlanError('Referenced file not found')
    return resolved


def load_brew_plan(path: str | Path, *, repo_root: str | Path):
    """Return plan, recipe and equipment without mutating either domain object."""
    root = Path(repo_root).resolve()
    data = _document(Path(path))
    plan = data.get('brew_plan')
    if not isinstance(plan, dict):
        raise BrewPlanError('Missing brew_plan')
    _required_text(plan, 'id')
    if plan.get('status') not in ('draft', 'ready', 'completed'):
        raise BrewPlanError('Invalid brew plan status')
    recipe = load_recipe(_repo_path(root, _required_text(plan, 'recipe_path')))
    equipment = load_equipment(_repo_path(root, _required_text(plan, 'equipment_path')))
    if recipe['recipe']['version'] != _required_text(plan, 'recipe_version'):
        raise BrewPlanError('Recipe version mismatch')
    if equipment['equipment']['id'] != _required_text(plan, 'equipment_id'):
        raise BrewPlanError('Equipment ID mismatch')
    volume = _number(plan.get('intended_packaged_volume_l'), 'intended_packaged_volume_l')
    if volume != float(recipe['targets']['packaged_volume_l']):
        raise BrewPlanError('Plan packaged volume differs from recipe target; explicit scaling not supported')
    return {'plan': data, 'recipe': recipe, 'equipment': equipment,
            'warnings': [
                'Equipment parameters are unverified third-party presets.',
                'Legacy equipment and water context in recipe has not been migrated.',
                'No ingredient scaling, water recalculation or controller synchronization performed.',
            ]}
