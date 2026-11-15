"""Offline export of controller programs for the Braumeister Bridge and HA."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
import unicodedata

from .recipe import RecipeError, load_recipe, validate_recipe


def _integer(value, low, high, field):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value != int(value) or not low <= value <= high):
        raise RecipeError(f"{field}: whole number from {low} to {high} required")
    return int(value)


def build_bridge_export(recipes):
    """Return HA service data and a separate report; never contact a device."""
    if not 1 <= len(recipes) <= 9:
        raise RecipeError("Bridge export requires 1 to 9 recipes")
    result, reports = [], []
    for source in recipes:
        validate_recipe(source)
        warnings = []
        original = source['recipe']['name'].strip()
        name = original
        for old, new in {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'}.items():
            name = name.replace(old, new)
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
        name = ''.join(c for c in name if 32 <= ord(c) <= 126 and c != ';').strip()[:14].rstrip()
        if not name:
            raise RecipeError("Recipe name has no usable ASCII characters")
        if name != original:
            warnings.append(f"Device name changed: {original!r} -> {name!r}")
        mash, boil = source['mash'], source['boil']
        if not 1 <= len(mash['steps']) <= 5:
            raise RecipeError("Bridge supports 1 to 5 mash rests")
        duration = _integer(boil['duration_min'], 1, 180, 'boil.duration_min')
        hops = []
        for addition in boil.get('additions', []):
            # Same hop classification as HBAC's existing BeerJSON exporter.
            if 'alpha_acid_percent' in addition:
                hops.append(_integer(addition['remaining_min'], 1, duration, 'hop.remaining_min'))
            else:
                warnings.append(f"Non-hop addition not transferred: {addition['ingredient']}")
        if len(hops) > 6:
            raise RecipeError("Bridge supports at most 6 hop additions")
        result.append({
            'name': name,
            'mash_in_temperature': _integer(mash['mash_in_temperature_c'], 20, 80, 'mash_in_temperature'),
            'rests': [{'temperature': _integer(s['temperature_c'], 20, 80, 'rest.temperature'),
                       'minutes': _integer(s['duration_min'], 1, 180, 'rest.minutes')} for s in mash['steps']],
            'boil_minutes': duration,
            'boil_temperature': _integer(boil.get('temperature_c', 103), 95, 105, 'boil.temperature_c'),
            'hop_additions': hops,
        })
        if 'temperature_c' not in boil:
            warnings.append('Boil temperature not supplied; Bridge default 103 C used')
        reports.append({'source_name': original, 'device_name': name, 'warnings': warnings})
    return {'recipes': result}, {
        'format': 'homebrew-as-code/bridge-export-report-v1',
        'replaces_all_device_recipes': True,
        'not_transferred': ['ingredient names and amounts', 'water chemistry', 'fermentation',
                            'packaging', 'targets', 'flameout contact time'],
        'hop_classification': 'Boil additions containing alpha_acid_percent are treated as hops',
        'recipes': reports,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Export Braumeister Bridge JSON for HA (offline)')
    parser.add_argument('paths', nargs='+', help='1 to 9 HBAC recipe YAML files, in device slot order')
    parser.add_argument('-o', '--output', required=True, help='Output .json file (HA action data)')
    args = parser.parse_args(argv)
    output = Path(args.output)
    report_path = output.with_suffix('.report.json')
    try:
        if output.suffix.lower() != '.json' or output == report_path:
            raise RecipeError('Output must end in .json and must not end in .report.json')
        inputs = {Path(p).resolve() for p in args.paths}
        if output.resolve() in inputs or report_path.resolve() in inputs:
            raise RecipeError('Output must not overwrite an input recipe')
        document, report = build_bridge_export([load_recipe(p) for p in args.paths])
        output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (RecipeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'Exported {len(document["recipes"])} recipe(s) to {output}. Report: {report_path}')
    print('WARNING: Upload replaces ALL device recipes. Review the export report before uploading.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
