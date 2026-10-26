"""Explicit recipe-bound exchange decisions; never mutate canonical recipe data."""
from copy import deepcopy
import math


def number(value, label, *, zero=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (value == 0 and not zero):
        raise ValueError(label + ' must be finite and ' + ('nonnegative' if zero else 'positive'))
    return value


def export_recipe(recipe, settings):
    result = deepcopy(recipe)
    profile = settings.get('export_profile')
    if profile is None:
        return result, [], [], None
    required = {'recipe_id', 'recipe_version', 'original_gravity_plato', 'boil_controller_temperature_c',
                'fermentation_steps', 'maturation_steps'}
    if not isinstance(profile, dict) or set(profile) != required:
        raise ValueError('Export profile requires exactly the documented fields')
    if (profile['recipe_id'], profile['recipe_version']) != (recipe['recipe']['id'], recipe['recipe']['version']):
        raise ValueError('Export profile recipe ID/version mismatch')
    plato = number(profile['original_gravity_plato'], 'Export original gravity')
    temperature = number(profile['boil_controller_temperature_c'], 'Controller boil setpoint')
    if plato > 40 or temperature > 110:
        raise ValueError('Export gravity or controller temperature outside supported range')
    result['targets']['original_gravity_plato'] = plato
    result['boil']['temperature_c'] = temperature
    stages = []
    for kind, fields in (
        ('fermentation_steps', {'temperature_c', 'duration_hours'}),
        ('maturation_steps', {'temperature_c', 'duration_days', 'pressure_bar'}),
    ):
        rows = profile[kind]
        if not isinstance(rows, list) or len(rows) > 10:
            raise ValueError(kind + ' must contain at most ten steps')
        mapped = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != fields:
                raise ValueError(kind + ': explicit units and only documented fields required')
            temp = row['temperature_c']
            if type(temp) not in (int, float) or not math.isfinite(temp) or not -5 <= temp <= 40:
                raise ValueError(kind + ': temperature outside supported range')
            duration_key = 'duration_hours' if kind == 'fermentation_steps' else 'duration_days'
            step = {'sorting': index, 'temperature': temp,
                    'duration': number(row[duration_key], duration_key)}
            if kind == 'fermentation_steps':
                step['time'] = 0
            else:
                step['pressure'] = number(row['pressure_bar'], 'pressure_bar', zero=True)
            mapped.append(step)
        stages.append(mapped)
    return result, stages[0], stages[1], deepcopy(profile)
