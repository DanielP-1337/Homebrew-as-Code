"""Offline, loss-aware MySpeidel private GET -> BeerXML 1.0 experiment.

No HTTP, no identity merging, no implicit compatibility guarantees.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from .myspeidel_put_roundtrip import private_file, read_backup

FORMAT = 'homebrew-as-code/myspeidel-beerxml-golden-v1'


def number(value, label):
    if isinstance(value, bool) or value is None:
        raise ValueError(f'Missing numeric {label}')
    try:
        result = Decimal(str(value).replace(',', '.').strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f'Invalid numeric {label}') from None
    if not result.is_finite() or result < 0:
        raise ValueError(f'Invalid numeric {label}')
    return str(result)


def put(parent, name, value):
    ET.SubElement(parent, name).text = str(value)


def catalog(recipe, category, uid):
    refs = recipe.get('references')
    items = refs.get(category) if isinstance(refs, dict) else None
    if not isinstance(items, dict):
        raise ValueError('Missing reference category: ' + category)
    record = items.get(uid)
    if not isinstance(record, dict):
        raise ValueError('Missing referenced ingredient: ' + category)
    return record


def _used(container, label):
    if not isinstance(container, list):
        raise ValueError('Missing list: ' + label)
    if not all(isinstance(x, dict) for x in container):
        raise ValueError('Malformed list: ' + label)
    return container


def export(recipe, title, *, batch_size, boil_size, assumed_yield, malt_color_overrides=None,
           mash_in_temp=None, mash_steps=None, yeast_type=None, yeast_form=None,
           yeast_amount_kg=None):
    """Export known recipe fields and report every unsupported semantic explicitly."""
    if not isinstance(recipe, dict) or not isinstance(title, str) or not title.strip():
        raise ValueError('Invalid recipe or export title')
    mash = recipe.get('mashing')
    boil = recipe.get('boil')
    if not isinstance(mash, dict) or not isinstance(boil, dict):
        raise ValueError('Missing mashing/boil operations')
    adds = mash.get('adds')
    if not isinstance(adds, dict):
        raise ValueError('Missing mashing.adds')
    malt_rows = _used(adds.get('malts'), 'mashing.adds.malts')
    steps = _used(boil.get('steps'), 'boil.steps')
    # BeerXML VERSION=1 for each recipe and ingredient object.
    root = ET.Element('RECIPES')
    r = ET.SubElement(root, 'RECIPE')
    for k, v in [('NAME', title.strip()), ('VERSION', '1'), ('TYPE', 'All Grain'),
                 ('BREWER', 'Homebrew-as-Code')]:
        put(r, k, v)
    duration = number(boil.get('boiling_duration'), 'boil.boiling_duration')
    put(r, 'BATCH_SIZE', number(batch_size, 'batch_size_l'))
    put(r, 'BOIL_SIZE', number(boil_size, 'boil_size_l'))
    put(r, 'BOIL_TIME', duration)
    fermentables = ET.SubElement(r, 'FERMENTABLES')
    if not malt_rows:
        raise ValueError('No malt ingredients to export')
    overrides = malt_color_overrides or {}
    if not isinstance(overrides, dict) or any(type(k) is not int or k < 0 or k >= len(malt_rows) for k in overrides):
        raise ValueError('Invalid malt color overrides')
    used_overrides = []
    for index, item in enumerate(malt_rows):
        uid = item.get('malt_uuid')
        ref = catalog(recipe, 'malts', uid)
        name = ref.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Missing malt name; cannot safely export')
        cloud_color = ref.get('color')
        has_cloud_color = cloud_color is not None and str(cloud_color).strip() != ''
        if index in overrides and has_cloud_color:
            raise ValueError(f'Malt color override not permitted: cloud value exists at index {index}')
        if index in overrides:
            color = number(overrides[index], f'malt[{index}].explicit_color_EBC')
            if Decimal(color) <= 0:
                raise ValueError('Malt override color must be positive')
            used_overrides.append({'malt_index': index, 'name': name,
                                   'color_ebc': color, 'source': 'manual_web_form_evidence'})
        else:
            color = number(cloud_color, f'malt[{index}].color_EBC')
        f = ET.SubElement(fermentables, 'FERMENTABLE')
        for key, val in [('NAME', name), ('VERSION', '1'), ('TYPE', 'Grain'),
                         ('AMOUNT', number(item.get('amount'), f'malt[{index}].amount')),
                         ('YIELD', number(ref.get('yield', assumed_yield), 'malt.yield')),
                         ('COLOR', str(Decimal(color) / Decimal('1.97')))]:
            put(f, key, val)
    hops = ET.SubElement(r, 'HOPS')
    hop_count = 0
    for i, step in enumerate(steps):
        step_adds = step.get('adds')
        if not isinstance(step_adds, dict):
            raise ValueError('Missing boil step additions')
        for j, item in enumerate(_used(step_adds.get('hops', []), f'boil.steps[{i}].adds.hops')):
            ref = catalog(recipe, 'hops', item.get('hop_uuid'))
            name = ref.get('name')
            if not isinstance(name, str) or not name.strip():
                raise ValueError('Missing hop name; cannot safely export')
            # Time must be explicit: never invent boil times or misinterpret step position.
            time = step.get('duration')
            if time is None:
                time = step.get('hopping_duration')
            if time is None:
                raise ValueError(f'Missing boil step time at index {i}; no guessed hop timing')
            h = ET.SubElement(hops, 'HOP')
            for key, val in [('NAME', name), ('VERSION', '1'),
                             ('ALPHA', number(item.get('acid', ref.get('acid')), f'hop[{i}/{j}].acid')),
                             ('AMOUNT', str(Decimal(number(item.get('amount'), f'hop[{i}/{j}].amount')) / 1000)),
                             ('USE', 'Boil'), ('TIME', number(time, f'boil.steps[{i}].duration'))]:
                put(h, key, val)
            hop_count += 1
    # Mash temperature schedules can be supplied as explicit, traceable web-form
    # observations. No time/temperature or infusion-water volumes are guessed.
    mapped = []
    if mash_in_temp is not None or mash_steps:
        if mash_in_temp is None or not mash_steps:
            raise ValueError('Mash export requires both mash-in temperature and mash steps')
        mash_node = ET.SubElement(r, 'MASH')
        put(mash_node, 'NAME', 'Observed MySpeidel mash schedule')
        put(mash_node, 'VERSION', '1')
        put(mash_node, 'GRAIN_TEMP', number(mash_in_temp, 'mash_in_temp'))
        ms = ET.SubElement(mash_node, 'MASH_STEPS')
        for i, pair in enumerate(mash_steps):
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise ValueError('Expected mash step temperature and minutes')
            temp, minutes = (number(v, f'mash_step[{i}]') for v in pair)
            if Decimal(temp) <= 0 or Decimal(minutes) <= 0:
                raise ValueError('Mash step temperature and duration must be positive')
            step_node = ET.SubElement(ms, 'MASH_STEP')
            for key, value in [('NAME', f'Rest {i+1}'), ('VERSION', '1'),
                               ('TYPE', 'Temperature'), ('STEP_TEMP', temp),
                               ('STEP_TIME', minutes)]:
                put(step_node, key, value)
            mapped.append({'temperature_c': temp, 'duration_min': minutes,
                           'source': 'manual_web_form_evidence'})
    # Cloud yeast identity is resolved only from the same recipe's references.
    yeast_rows = _used(((recipe.get('fermentation') or {}).get('adds') or {}).get('yeasts', []),
                      'fermentation.adds.yeasts')
    yeast_count = 0
    yeast_skipped = []
    if yeast_rows:
        if not yeast_type or not yeast_form or yeast_amount_kg is None:
            yeast_skipped.append('Yeast type/form/BeerXML amount not confirmed; no BeerXML yeast objects emitted')
        else:
            if yeast_type not in ('Ale', 'Lager', 'Wheat', 'Wine', 'Champagne'):
                raise ValueError('Invalid explicit yeast type')
            if yeast_form not in ('Liquid', 'Dry', 'Slant', 'Culture'):
                raise ValueError('Invalid explicit yeast form')
            ys = ET.SubElement(r, 'YEASTS')
            for i, row in enumerate(yeast_rows):
                ref = catalog(recipe, 'yeasts', row.get('yeast_uuid'))
                yeast_name = ref.get('name')
                if not isinstance(yeast_name, str) or not yeast_name.strip():
                    yeast_skipped.append(f'Yeast [{i}] missing Cloud reference name')
                    continue
                y = ET.SubElement(ys, 'YEAST')
                for key, value in [('NAME', yeast_name), ('VERSION', '1'),
                                   ('TYPE', yeast_type), ('FORM', yeast_form),
                                   ('AMOUNT', number(yeast_amount_kg, 'explicit_yeast_amount_kg')),
                                   ('AMOUNT_IS_WEIGHT', 'TRUE')]:
                    put(y, key, value)
                # BeerXML AMOUNT uses kg/l depending on AMOUNT_IS_WEIGHT;
                # do not guess a unit for a vendor quantity.
                yeast_count += 1
    # Water is not represented as mash/sparge volumes in BeerXML 1.0.
    # Never translate it into WATER mineral profile or guessed INFUSE_AMOUNT.
    water_add = adds.get('water')
    water_note = ('MySpeidel mashing.adds.water is present; not representable as '
                  'separate mash/sparge volumes in standard BeerXML 1.0') if water_add is not None else \
                 'No explicit mashing.adds.water value present'
    warnings = [
        'BeerXML conversion is experimental; do not infer MySpeidel import acceptance.',
        'UUIDs, account-specific catalog identity and recipe ownership are not exported.',
        'Malt amounts assumed kilograms and hop amounts assumed grams based on observed MySpeidel web/cloud examples.',
        'BATCH_SIZE and BOIL_SIZE are explicit CLI values, not extracted from backup.',
        'Malt YIELD may be an explicitly assumed value; verify all malt yield values.',
        'Manual color overrides are based on separately observed web form values, not authoritative Cloud identity.',
        'Malt color interpreted as EBC and converted to BeerXML SRM / 1.97; verify vendor units.',
        'Water treatment and equipment-specific settings are not mapped.',
        water_note, *yeast_skipped,
        'Mash steps are emitted only from explicit web-form evidence; fermentation schedule and maturation are not mapped.',
        'Original recipe name retained only in local report; export receives distinct title.',
    ]
    return ET.tostring(root, encoding='utf-8', xml_declaration=True), {
        'format': FORMAT, 'status': 'PARTIAL_EXPORT', 'export_name': title,
        'source_name': recipe.get('name'), 'malt_count': len(malt_rows),
        'hop_count': hop_count, 'yeast_count': yeast_count,
        'mash_steps': mapped, 'mash_schedule_source': 'manual_web_form_evidence' if mapped else 'unavailable',
        'malt_color_overrides': used_overrides, 'warnings': warnings,
        'unsupported_fields': ([ ] if mapped else ['mashing.rest', 'mashing.steps']) +
                              ['mashing.adds.water', 'fermentation', 'maturation', 'machine_type',
                               'references.water_types'],
    }


def snapshot(recipe):
    """Stable business projections, without treating equal names as equal IDs."""
    mash = recipe.get('mashing') or {}
    boil = recipe.get('boil') or {}
    adds = mash.get('adds') or {}
    malts = []
    for item in adds.get('malts') or []:
        ref = catalog(recipe, 'malts', item.get('malt_uuid'))
        malts.append((str(ref.get('name')), number(item.get('amount'), 'malt.amount')))
    hops = []
    for step in boil.get('steps') or []:
        for item in (step.get('adds') or {}).get('hops') or []:
            ref = catalog(recipe, 'hops', item.get('hop_uuid'))
            hops.append((str(ref.get('name')), number(item.get('amount'), 'hop.amount'),
                         number(item.get('acid', ref.get('acid')), 'hop.acid')))
    return {'malts': sorted(malts), 'hops': sorted(hops),
            'boil_duration': number(boil.get('boiling_duration'), 'boil.boiling_duration')}


def compare(before, after):
    a, b = snapshot(before), snapshot(after)
    details = {}
    for field in a:
        details[field] = {'status': 'EQUIVALENT' if a[field] == b[field] else 'CHANGED',
                          'original': a[field], 'imported': b[field]}
    return {'format': FORMAT, 'status': 'EQUIVALENT_FOR_CHECKED_FIELDS' if all(
        x['status'] == 'EQUIVALENT' for x in details.values()) else 'DIFFERENCES_FOUND',
        'checked_fields': details, 'unverified': ['water', 'mash rests', 'yeasts',
                                                'fermentation', 'equipment', 'ingredient UUID identity'],
        'note': 'This compares only selected semantic fields; equivalent does not mean lossless.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Offline MySpeidel BeerXML Golden Roundtrip')
    sub = parser.add_subparsers(dest='command', required=True)
    out = sub.add_parser('export')
    out.add_argument('--backup', required=True)
    out.add_argument('--xml', required=True)
    out.add_argument('--report', required=True)
    out.add_argument('--name', default='HBAC BeerXML Roundtrip - Weizen 38')
    out.add_argument('--batch-size-liters', required=True)
    out.add_argument('--boil-size-liters', required=True)
    out.add_argument('--assumed-malt-yield-percent', required=True)
    out.add_argument('--malt-color-override', action='append', default=[], metavar='INDEX=EBC',
                     help='Explicit web-form EBC color for a malt missing Cloud color; 0-based malt index')
    out.add_argument('--mash-in-temp', help='Explicit Celsius mash-in temperature from web form')
    out.add_argument('--mash-step', action='append', default=[], metavar='TEMP:MIN',
                     help='Explicit web-form rest temperature and duration; repeat in order')
    out.add_argument('--yeast-type', choices=['Ale', 'Lager', 'Wheat', 'Wine', 'Champagne'])
    out.add_argument('--yeast-form', choices=['Liquid', 'Dry', 'Slant', 'Culture'])
    out.add_argument('--yeast-amount-kg', help='Manually verified yeast mass in kilograms')
    chk = sub.add_parser('compare')
    chk.add_argument('--original', required=True)
    chk.add_argument('--imported', required=True)
    chk.add_argument('--report', required=True)
    args = parser.parse_args(argv)
    try:
        report_path = private_file(args.report)
        if args.command == 'export':
            inp = private_file(args.backup, must_exist=True)
            xml_path = private_file(args.xml)
            if xml_path.suffix.lower() != '.xml':
                raise ValueError('Output must have .xml extension')
            _, recipe, sha = read_backup(inp)
            overrides = {}
            for spec in args.malt_color_override:
                parts = spec.split('=', 1)
                if len(parts) != 2 or not parts[0].isdecimal():
                    raise ValueError('Expected --malt-color-override INDEX=EBC')
                idx = int(parts[0])
                if idx in overrides:
                    raise ValueError('Duplicate malt color override index')
                overrides[idx] = parts[1]
            rest_pairs = []
            for step in args.mash_step:
                parts = step.split(':')
                if len(parts) != 2:
                    raise ValueError('Expected --mash-step TEMP:MIN')
                rest_pairs.append(parts)
            data, report = export(recipe, args.name, malt_color_overrides=overrides,
                                  mash_in_temp=args.mash_in_temp, mash_steps=rest_pairs,
                                  yeast_type=args.yeast_type, yeast_form=args.yeast_form,
                                  yeast_amount_kg=args.yeast_amount_kg,
                                  batch_size=args.batch_size_liters,
                                  boil_size=args.boil_size_liters,
                                  assumed_yield=args.assumed_malt_yield_percent)
            ET.fromstring(data)
            report['source_sha256'] = sha
            report['xml_sha256'] = hashlib.sha256(data).hexdigest()
            xml_path.parent.mkdir(parents=True, exist_ok=True)
            with xml_path.open('xb') as f:
                f.write(data)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open('x', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print('Offline PARTIAL BeerXML export; manual review required; no HTTP requests.')
        else:
            a_path = private_file(args.original, must_exist=True)
            b_path = private_file(args.imported, must_exist=True)
            a_id, a, _ = read_backup(a_path)
            b_id, b, _ = read_backup(b_path)
            if a_id == b_id:
                raise ValueError('Original and imported backups have same recipe UUID')
            report = compare(a, b)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with report_path.open('x', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print('Offline semantic comparison completed; no HTTP requests.')
        return 0
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        print(f'BeerXML roundtrip stopped: {type(exc).__name__}: {str(exc)[:150]}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
