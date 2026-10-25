"""Offline, conservative BeerXML cross-application comparison.

Comparison uses only standard BeerXML fields. Brewfather export is private input;
no proprietary identifiers or complete third-party examples enter the repository.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


class RoundtripError(ValueError):
    """Invalid or unsupported comparison input."""


def _number(text: str | None, path: str) -> Decimal:
    if text is None or not text.strip():
        raise RoundtripError(f'Missing numeric value: {path}')
    try:
        value = Decimal(text.strip())
    except InvalidOperation as exc:
        raise RoundtripError(f'Invalid numeric value: {path}') from exc
    if not value.is_finite():
        raise RoundtripError(f'Nonfinite numeric value: {path}')
    return value


def _read(path: Path) -> ET.Element:
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise RoundtripError('Missing or oversized XML input')
    data = path.read_bytes()
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise RoundtripError('DTD and entities are not accepted')
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise RoundtripError('Malformed BeerXML') from exc
    if root.tag != 'RECIPES' or len(root.findall('RECIPE')) != 1:
        raise RoundtripError('Expected exactly one RECIPES/RECIPE')
    return root.find('RECIPE')


def _entries(recipe: ET.Element, container: str, child: str, fields: tuple[str, ...]):
    result = Counter()
    for row in recipe.findall(f'./{container}/{child}'):
        values = []
        for field in fields:
            val = row.findtext(field)
            if field in {'AMOUNT', 'TIME', 'ALPHA', 'STEP_TEMP', 'STEP_TIME', 'COLOR', 'YIELD'}:
                values.append(str(_number(val, f'{container}/{child}/{field}').normalize()))
            else:
                values.append((val or '').strip().casefold())
        result[tuple(values)] += 1
    return result


def _format_entries(entries: Counter):
    return [{'values': list(key), 'count': count} for key, count in sorted(entries.items())]


def compare_xml(source: ET.Element, reexport: ET.Element) -> dict:
    """Compare business fields; flag yeast mass convention instead of normalizing unsafely."""
    areas = {
        'fermentables': ('FERMENTABLES', 'FERMENTABLE', ('NAME', 'TYPE', 'AMOUNT', 'YIELD', 'COLOR')),
        'hops': ('HOPS', 'HOP', ('NAME', 'ALPHA', 'AMOUNT', 'USE', 'TIME')),
        'spices': ('MISCS', 'MISC', ('NAME', 'TYPE', 'USE', 'TIME', 'AMOUNT', 'AMOUNT_IS_WEIGHT')),
        'mash_steps': ('MASH/MASH_STEPS', 'MASH_STEP', ('STEP_TEMP', 'STEP_TIME')),
    }
    results = {}
    for label, (parent, child, fields) in areas.items():
        original = _entries(source, parent, child, fields)
        after = _entries(reexport, parent, child, fields)
        results[label] = {'status': 'MATCH' if original == after else 'DIFFERENT',
                          'original': _format_entries(original), 'reexport': _format_entries(after)}
    for label, key in [('batch_size_l', 'BATCH_SIZE'), ('boil_size_l', 'BOIL_SIZE'),
                       ('boil_duration_min', 'BOIL_TIME'), ('efficiency_percent', 'EFFICIENCY'),
                       ('carbonation_volumes', 'CARBONATION')]:
        orig_raw, after_raw = source.findtext(key), reexport.findtext(key)
        if orig_raw is None or after_raw is None:
            status = 'NOT_OBSERVED'
        else:
            status = 'MATCH' if _number(orig_raw, key) == _number(after_raw, key) else 'DIFFERENT'
        results[label] = {'status': status, 'original': orig_raw, 'reexport': after_raw}
    # Gravity may be rounded on reexport. Do not declare exact equality without it.
    for key in ('OG', 'FG', 'IBU', 'PRIMARY_AGE', 'PRIMARY_TEMP'):
        a, b = source.findtext(key), reexport.findtext(key)
        status = 'NOT_OBSERVED' if a is None or b is None else ('MATCH' if a == b else 'DIFFERENT')
        results[key.lower()] = {'status': status, 'original': a, 'reexport': b,
                                'note': 'Application-computed or profile-derived; not evidence of canonical recipe equivalence.'}
    yeast_before = source.findall('./YEASTS/YEAST')
    yeast_after = reexport.findall('./YEASTS/YEAST')
    yeast_entries = []
    if len(yeast_before) != len(yeast_after):
        yeast_status = 'DIFFERENT'
    else:
        yeast_status = 'MATCH'
    for old, new in zip(yeast_before, yeast_after):
        a, b = old.findtext('AMOUNT'), new.findtext('AMOUNT')
        flag_a, flag_b = old.findtext('AMOUNT_IS_WEIGHT'), new.findtext('AMOUNT_IS_WEIGHT')
        name_a, name_b = old.findtext('NAME'), new.findtext('NAME')
        if flag_a is None or flag_b is None:
            status = 'UNIT_SEMANTICS_UNVERIFIED'
        elif name_a != name_b or _number(a, 'YEAST/AMOUNT') != _number(b, 'YEAST/AMOUNT') or flag_a.casefold() != flag_b.casefold():
            status = 'DIFFERENT'
        else:
            status = 'MATCH'
        if status != 'MATCH':
            yeast_status = 'UNIT_SEMANTICS_UNVERIFIED' if status == 'UNIT_SEMANTICS_UNVERIFIED' else 'DIFFERENT'
        yeast_entries.append({'name_original': name_a, 'name_reexport': name_b,
                              'amount_original': a, 'amount_reexport': b,
                              'weight_flag_original': flag_a, 'weight_flag_reexport': flag_b,
                              'status': status})
    results['yeast'] = {'status': yeast_status, 'entries': yeast_entries}
    return {
        'format': 'homebrew-as-code/beerxml-cross-app-v1',
        'status': 'SEMANTIC_DIFFERENCES_OR_GAPS' if any(v['status'] != 'MATCH' for v in results.values()) else 'MATCH_FOR_CHECKED_FIELDS',
        'fields': results,
        'limitations': [
            'Comparison covers selected fields; it is not a full BeerXML conformance or lossless roundtrip proof.',
            'Do not equate matching ingredient names with stable vendor catalog identities.',
            'BeerXML yeast mass must not be inferred from DISPLAY_AMOUNT or unmarked AMOUNT.',
            'Brewfather equipment water splits and fermentation defaults must not be promoted to canonical YAML.',
            'Source XML and Brewfather reexport remain private; this report contains ingredient names and quantities.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline cross-application BeerXML semantic comparison')
    parser.add_argument('--source-xml', required=True)
    parser.add_argument('--reexport-xml', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args(argv)
    try:
        source, reexport, report = map(Path, (args.source_xml, args.reexport_xml, args.report))
        if report.exists():
            raise RoundtripError('Report exists; refusing overwrite')
        if '.local' not in report.parts:
            raise RoundtripError('Report must be stored under .local/')
        data = compare_xml(_read(source), _read(reexport))
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open('x', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        print('Offline comparison written; review differences and yeast unit flags.')
        return 0
    except (OSError, RoundtripError) as exc:
        print(f'Comparison stopped: {type(exc).__name__}: {str(exc)[:160]}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
