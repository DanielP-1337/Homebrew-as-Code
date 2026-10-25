"""Offline comparison of YAML-derived BeerXML with manually observed MySpeidel fields.

Observations are user-entered from UI, not trusted API/identity evidence.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET


FIELDS = ('batch_size_l', 'boil_duration_min', 'mash_in_c', 'og_sg',
          'bitterness_ibu', 'color_ebc', 'yeast_amount_g')


def num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        d = Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        raise ValueError('Observation contains invalid numeric value') from None
    if not d.is_finite() or d < 0:
        raise ValueError('Observation contains invalid numeric value')
    return d


def report(xml_bytes: bytes, observations: dict) -> dict:
    root = ET.fromstring(xml_bytes)
    recipe = root.find('RECIPE')
    if root.tag != 'RECIPES' or recipe is None:
        raise ValueError('Expected BeerXML RECIPES/RECIPE')
    if not isinstance(observations, dict) or set(observations) - set(FIELDS):
        raise ValueError('Unknown observation fields')
    source = {
        'batch_size_l': recipe.findtext('BATCH_SIZE'),
        'boil_duration_min': recipe.findtext('BOIL_TIME'),
        'mash_in_c': None,  # No valid equivalent in core BeerXML; do not equate first rest.
        'og_sg': recipe.findtext('OG'),
        'bitterness_ibu': None,  # Device recalculates; target only in NOTES.
        'color_ebc': None,  # Device recalculates from grist properties.
        'yeast_amount_g': (str(num(recipe.findtext('./YEASTS/YEAST/AMOUNT')) * 1000)
                            if recipe.findtext('./YEASTS/YEAST/AMOUNT') and
                            (recipe.findtext('./YEASTS/YEAST/AMOUNT_IS_WEIGHT') or '').upper() == 'TRUE' else None),
    }
    details = {}
    for key in FIELDS:
        expected, actual = num(source[key]), num(observations.get(key))
        if actual is None:
            status = 'NOT_OBSERVED'
        elif expected is None:
            status = 'UNVERIFIED_MAPPING_OR_RECALCULATED'
        else:
            tolerance = Decimal('.00002') if key == 'og_sg' else Decimal('.01')
            status = 'MATCH' if abs(expected - actual) <= tolerance else 'DIFFERENT'
        details[key] = {'status': status, 'exported': str(expected) if expected is not None else None,
                        'myspeidel_observed': str(actual) if actual is not None else None}
    return {'status': 'OFFLINE_MANUAL_OBSERVATIONS_ONLY', 'fields': details,
            'notes': ['No cloud API calls, no ingredient identity merging.',
                      'IBU and EBC calculations by MySpeidel are not modeled.',
                      'Mash-in temperature has no confirmed BeerXML mapping.',
                      'UI values are observations, not measurements.']}


def main(argv=None):
    p = argparse.ArgumentParser(description='Offline MySpeidel semantic comparison')
    p.add_argument('--xml', required=True)
    p.add_argument('--observations-json', required=True)
    p.add_argument('--report', required=True)
    a = p.parse_args(argv)
    try:
        output = Path(a.report)
        if output.exists():
            raise ValueError('Output exists; refusing overwrite')
        result = report(Path(a.xml).read_bytes(), json.loads(Path(a.observations_json).read_text(encoding='utf-8')))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print('Offline MySpeidel semantic comparison written.')
        return 0
    except (OSError, ValueError, TypeError, ET.ParseError) as exc:
        p.exit(1, f'Comparison failed: {type(exc).__name__}: {str(exc)[:180]}\n')


if __name__ == '__main__':
    raise SystemExit(main())
