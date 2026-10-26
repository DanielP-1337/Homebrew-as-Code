"""Offline batch measurements and explicit actual-yield totals. No API or tax filing."""
import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path
from uuid import uuid4

from .brew_plan import load_brew_plan
from .myspeidel_put_roundtrip import digest, private_file, write_new

FORMAT = 'homebrew-as-code/brew-day-v1'
STAGES = ('pre_boil_before_adjustment', 'pre_boil_after_adjustment', 'post_boil', 'fermentation')


def number(value, label, minimum, maximum):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{label} must be finite and between {minimum} and {maximum}')


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be non-empty text')


def calendar_date(value):
    text(value, 'date')
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('Use YYYY-MM-DD dates')
    return parsed


def new_record(bundle, brew_date, *, record_kind="real"):
    calendar_date(brew_date)
    recipe = bundle['recipe']['recipe']
    return {
        'format': FORMAT, 'batch_id': str(uuid4()), 'brew_date': brew_date,
        'recipe_id': recipe['id'], 'recipe_version': recipe['version'],
        'recipe_name': recipe.get('name', recipe['id']), 'record_kind': record_kind,
        'brew_plan_id': bundle['plan']['brew_plan']['id'],
        'source_sha256': digest(bundle), 'measurements': [],
        'actual_yield': {'production_date': None, 'produced_beer_l': None,
                         'packaged_beer_l': None, 'note': ''},
        'notes': '',
    }


def validate(record):
    if not isinstance(record, dict) or record.get('format') != FORMAT:
        raise ValueError('Expected brew-day-v1 record')
    for field in ('batch_id', 'recipe_id', 'recipe_version', 'brew_plan_id', 'source_sha256'):
        text(record.get(field), field)
    if record.get('record_kind') not in (None, 'real', 'test'):
        raise ValueError('record_kind must be real or test')
    brew_date = calendar_date(record['brew_date'])
    rows = record['measurements']
    if not isinstance(rows, list):
        raise ValueError('measurements must be a list')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get('stage') not in STAGES:
            raise ValueError('Unknown measurement stage')
        moment = datetime.fromisoformat(row['measured_at'])
        if moment.utcoffset() is None or moment.date() < brew_date:
            raise ValueError('Measurement needs timezone and cannot precede brew date')
        key = (row['stage'], moment)
        if key in seen:
            raise ValueError('Duplicate measurement stage and instant')
        seen.add(key)
        text(row.get('instrument'), 'instrument')
        has_value = False
        for field, low, high in (('raw_plato', -10, 40), ('corrected_plato', -10, 40),
                                 ('sample_temperature_c', -5, 110), ('volume_l', 0, 100000),
                                 ('volume_temperature_c', -5, 110)):
            value = row.get(field)
            if value is not None:
                number(value, field, low, high)
                if field in ('raw_plato', 'corrected_plato', 'volume_l'):
                    has_value = True
                if field.endswith('plato') and row['stage'] != 'fermentation' and value < 0:
                    raise ValueError('Wort extract cannot be negative')
        if not has_value:
            raise ValueError('Measurement needs extract or volume')
        if row.get('raw_plato') is not None or row.get('corrected_plato') is not None:
            if row.get('sample_temperature_c') is None:
                raise ValueError('Extract reading requires sample temperature')
        if row.get('corrected_plato') is not None:
            text(row.get('correction_method'), 'correction_method')
        if row.get('volume_l') is not None and row.get('volume_temperature_c') is None:
            raise ValueError('Volume requires its own measurement temperature')
    actual = record['actual_yield']
    if not isinstance(actual, dict):
        raise ValueError('actual_yield must be an object')
    for field in ('produced_beer_l', 'packaged_beer_l'):
        value = actual.get(field)
        if value is not None:
            number(value, field, 0, 100000)
    production_date = actual.get('production_date')
    if production_date is not None and calendar_date(production_date) < brew_date:
        raise ValueError('Production date cannot precede brew date')
    if actual.get('produced_beer_l') is not None and production_date is None:
        raise ValueError('Actual production requires an explicit production date')
    produced, packaged = actual.get('produced_beer_l'), actual.get('packaged_beer_l')
    if produced is not None and packaged is not None and packaged > produced:
        raise ValueError('Packaged volume exceeds produced beer volume')
    return record


def report(record):
    validate(record)
    by_stage = {stage: [r for r in record['measurements'] if r['stage'] == stage] for stage in STAGES}
    return {
        'format': 'homebrew-as-code/brew-day-report-v1', 'batch_id': record['batch_id'],
        'record_kind': record.get('record_kind') or 'unclassified',
        'measurements_by_stage': by_stage, 'actual_yield': record['actual_yield'],
        'missing_stages': [s for s, rows in by_stage.items() if not rows],
        'alcohol_abv_percent': None, 'efficiency_percent': None, 'upload_ready': False,
        'note': 'Measurements are observations, not recipe targets. Fermentation readings are apparent extract. No automatic temperature correction, final-gravity selection, ABV or efficiency calculation.',
    }


def year_summary(records, year):
    number(year, 'year', 1, 9999)
    if type(year) is not int:
        raise ValueError('year must be an integer')
    seen, included, unresolved = set(), [], []
    excluded_tests, unclassified = [], []
    for record in records:
        validate(record)
        batch_id = record['batch_id']
        if batch_id in seen:
            raise ValueError(f'Duplicate batch_id: {batch_id}')
        seen.add(batch_id)
        if record.get('record_kind') == 'test':
            excluded_tests.append(batch_id)
            continue
        if record.get('record_kind') != 'real':
            unclassified.append(batch_id)
            continue
        actual = record['actual_yield']
        when, volume = actual.get('production_date'), actual.get('produced_beer_l')
        if when is None:
            unresolved.append(batch_id)
        elif calendar_date(when).year == year:
            if volume is None:
                unresolved.append(batch_id)
            else:
                included.append({'batch_id': batch_id, 'production_date': when, 'produced_beer_l': volume})
    return {'format': 'homebrew-as-code/actual-production-summary-v1', 'year': year,
            'included_batches': included, 'known_produced_beer_l': sum(r['produced_beer_l'] for r in included),
            'unresolved_batches': unresolved, 'input_records': len(records),
            'excluded_test_batches': excluded_tests, 'unclassified_batches': unclassified,
            'scope': 'Supplied records only. Unknown dates remain unresolved; packaged and wort volumes are not added. No 12-Plato normalization, exemption determination or tax calculation.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    init.add_argument('--plan', default='brew-plans/weizen-nikolaus-brew-001.yaml')
    init.add_argument('--date', required=True)
    init.add_argument('--kind', choices=('test', 'real'), default='test')
    init.add_argument('--output', required=True)
    show = sub.add_parser('report')
    show.add_argument('--record', required=True)
    annual = sub.add_parser('year')
    annual.add_argument('--year', type=int, required=True)
    annual.add_argument('--records', nargs='+', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            bundle = load_brew_plan(args.plan, repo_root=Path.cwd())
            record = new_record(bundle, args.date, record_kind=args.kind)
            validate(record)
            write_new(private_file(args.output), record)
            print(f'Record kind: {record["record_kind"]}')
            print('Saved local batch record. Edit observations, then run report. No API requests.')
        elif args.command == 'report':
            record = json.loads(Path(args.record).read_text(encoding='utf-8-sig'))
            print(json.dumps(report(record), indent=2, ensure_ascii=False, allow_nan=False))
        else:
            records = [json.loads(Path(p).read_text(encoding='utf-8-sig')) for p in args.records]
            print(json.dumps(year_summary(records, args.year), indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f'Brew-day operation stopped: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
