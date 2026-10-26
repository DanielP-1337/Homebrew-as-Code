"""Guided local brew-day recording. No API requests or recipe modifications."""
import argparse
import copy
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from .brew_day import new_record, validate, report, calendar_date, STAGES
from .brew_plan import load_brew_plan
from .myspeidel_put_roundtrip import private_file, write_new

STAGE_LABELS = (
    'Before boiling, before gravity adjustment',
    'Before boiling, after gravity adjustment',
    'After boiling / final wort measurement',
    'Fermentation / apparent extract',
)


class Cancelled(Exception):
    """User left the current operation without saving."""


def ask(prompt):
    value = input(prompt).strip()
    if value.lower() == 'cancel':
        raise Cancelled()
    return value


def choose(title, labels):
    print(title)
    for index, label in enumerate(labels, 1):
        print(f'  {index}  {label}')
    while True:
        value = ask('Select number (Enter cancels): ')
        if not value:
            raise Cancelled()
        if value.isdigit() and 1 <= int(value) <= len(labels):
            return int(value) - 1
        print('Choose one of the displayed numbers.')


def numeric(label, *, minimum=None, maximum=None, allow_unknown=True):
    while True:
        suffix = ' (Enter = unknown)' if allow_unknown else ''
        value = ask(f'{label}{suffix}: ')
        if not value:
            if allow_unknown:
                return None
            print('A value is required here; type cancel to leave without saving.')
            continue
        try:
            result = float(value.replace(',', '.'))
            import math
            if not math.isfinite(result):
                raise ValueError()
            if minimum is not None and result < minimum:
                print(f'Enter a value of at least {minimum:g}.')
                continue
            if maximum is not None and result > maximum:
                print(f'Enter a value no greater than {maximum:g}.')
                continue
            return result
        except ValueError:
            print('Enter a finite number; decimal comma or point is accepted.')


def required(label, default=None):
    while True:
        suffix = f' [{default}]' if default is not None else ''
        value = ask(label + suffix + ': ')
        if value or default is not None:
            return value or default
        print('A value is required; type cancel to leave without saving.')


def dated(label, default, *, not_before=None):
    while True:
        value = required(label + ' (YYYY-MM-DD)', default)
        try:
            parsed = calendar_date(value)
            if not_before is not None and parsed < calendar_date(not_before):
                print(f'Date cannot precede brew date {not_before}.')
                continue
            return value
        except ValueError:
            print('Enter a calendar date as YYYY-MM-DD.')


def measured_at(record, stage):
    default = datetime.now().astimezone().isoformat(timespec='seconds')
    while True:
        value = required('Measured at (ISO timestamp with timezone)', default)
        try:
            moment = datetime.fromisoformat(value)
            if moment.utcoffset() is None:
                print('Include a timezone offset, for example +01:00.')
                continue
            if moment.date() < calendar_date(record['brew_date']):
                print(f"Measurement cannot precede brew date {record['brew_date']}.")
                continue
            if any(r['stage'] == stage and datetime.fromisoformat(r['measured_at']) == moment
                   for r in record['measurements']):
                print('This stage already has a measurement at that instant. Enter another timestamp.')
                continue
            return value
        except ValueError:
            print('Enter an ISO timestamp, for example 2026-10-26T14:00:00+01:00, or press Enter for the displayed time.')


def confirmed(record):
    validate(record)
    print(json.dumps(report(record), ensure_ascii=False, indent=2, allow_nan=False))
    if ask('Save these observations locally? [yes/NO]: ').lower() != 'yes':
        raise Cancelled()


def plans(root):
    result = []
    for path in sorted((root / 'brew-plans').glob('*.yaml')):
        try:
            bundle = load_brew_plan(path, repo_root=root)
            result.append((path, bundle))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            print(f'Skipped plan {path.name}: {exc}')
    return result


def read_record(path):
    raw = path.read_bytes()
    record = json.loads(raw.decode('utf-8-sig'))
    validate(record)
    return record, hashlib.sha256(raw).hexdigest()


def label(record):
    return (f'{record.get("recipe_name", record["recipe_id"])} | {record["brew_date"]} | '
            f'{(record.get("record_kind") or "unclassified").upper()} | {record["batch_id"]}')


def atomic_save(path, expected_hash, record):
    """Cooperating writers lock; stale reads fail; retain original bytes before replace."""
    path = private_file(str(path), must_exist=True)
    validate(record)
    lock = path.with_suffix(path.suffix + '.lock')
    temporary = path.with_name('.' + path.name + '.' + uuid4().hex + '.tmp')
    handle = lock.open('x', encoding='utf-8')
    try:
        with handle:
            try:
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != expected_hash:
                    raise ValueError('Record changed since selection; resume again before editing')
                original = json.loads(raw.decode('utf-8-sig'))
                for field in ('batch_id', 'recipe_id', 'recipe_version', 'brew_plan_id', 'source_sha256', 'brew_date'):
                    if original.get(field) != record.get(field):
                        raise ValueError(f'Cannot change batch identity: {field}')
                if original.get('record_kind') in ('real', 'test') and original['record_kind'] != record.get('record_kind'):
                    raise ValueError('Cannot change an established test/real classification')
                # batch_id is externally editable: never use it as a path component.
                history = path.parent / '.history' / hashlib.sha256(record['batch_id'].encode()).hexdigest()
                history.mkdir(parents=True, exist_ok=True)
                with (history / (uuid4().hex + '.json')).open('xb') as backup:
                    backup.write(raw)
                    backup.flush()
                    os.fsync(backup.fileno())
                with temporary.open('x', encoding='utf-8', newline='\n') as stream:
                    json.dump(record, stream, indent=2, ensure_ascii=False, allow_nan=False)
                    stream.write('\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    finally:
        lock.unlink(missing_ok=True)


def safe_save(path, expected_hash, record):
    # Only remove locks created by this operation, including on validation/conflict errors.
    lock = path.with_suffix(path.suffix + '.lock')
    if lock.exists():
        raise ValueError('Record is locked; check another recording process before retrying')
    atomic_save(path, expected_hash, record)


def start(root):
    available = plans(root)
    if not available:
        raise ValueError('No valid brew plans found')
    names = [f'{b["recipe"]["recipe"]["name"]} | {b["plan"]["brew_plan"]["id"]} | '
             f'{b["equipment"]["equipment"]["model"]}' for _, b in available]
    _, bundle = available[choose('Select recipe / brew plan', names)]
    kind = ('test', 'real')[choose('Select record type', ['TEST — excluded from annual production', 'REAL — actual brew'])]
    day = dated('Brew date', date.today().isoformat())
    record = new_record(bundle, day, record_kind=kind)
    print(label(record))
    if ask('Create this local batch record? [yes/NO]: ').lower() != 'yes':
        raise Cancelled()
    path = private_file(str(root / '.local' / 'brew-days' / f'{day}-{record["batch_id"]}.json'))
    write_new(path, record)
    print('Created:', path)
    print('Next: resume to record measurements. No API requests.')


def measurement(record):
    stage = STAGES[choose('Measurement stage', STAGE_LABELS)]
    moment = measured_at(record, stage)
    instrument = required('Instrument / measurement method')
    lower = -10 if stage == 'fermentation' else 0
    raw = numeric('Raw hydrometer reading (Plato; fermentation = apparent extract)', minimum=lower, maximum=40)
    temperature = numeric('Sample temperature (C)', minimum=-5, maximum=110, allow_unknown=raw is None)
    corrected = numeric('Temperature-corrected reading (Plato)', minimum=lower, maximum=40)
    if corrected is not None and temperature is None:
        temperature = numeric('Sample temperature required for corrected reading (C)', minimum=-5, maximum=110, allow_unknown=False)
    method = required('Correction method') if corrected is not None else None
    volume = numeric('Measured volume (L)', minimum=0, maximum=100000,
                     allow_unknown=raw is not None or corrected is not None)
    volume_temperature = numeric('Volume measurement temperature (C)', minimum=-5, maximum=110,
                                 allow_unknown=False) if volume is not None else None
    note = ask('Measurement note (optional): ')
    record['measurements'].append({'stage': stage, 'measured_at': moment, 'instrument': instrument,
        'raw_plato': raw, 'sample_temperature_c': temperature, 'corrected_plato': corrected,
        'correction_method': method, 'volume_l': volume, 'volume_temperature_c': volume_temperature,
        'note': note})


def actual_yield(record):
    print('Existing yield:', json.dumps(record['actual_yield'], ensure_ascii=False))
    print('Enter replacement yield values. Blank quantities mean unknown; they do not retain old values.')
    produced = numeric('Actual produced beer (L)', minimum=0, maximum=100000)
    packaged = numeric('Actual packaged beer (L)', minimum=0, maximum=produced if produced is not None else 100000)
    production_date = dated('Production date', date.today().isoformat(), not_before=record['brew_date']) if produced is not None else None
    record['actual_yield'] = {'produced_beer_l': produced, 'packaged_beer_l': packaged,
                             'production_date': production_date, 'note': ask('Yield measurement basis / note: ')}


def resume(root, selected=None):
    if selected:
        path = private_file(selected, must_exist=True)
        record, sha = read_record(path)
    else:
        available = []
        for path in sorted((root / '.local' / 'brew-days').glob('*.json')):
            try:
                record, sha = read_record(path)
                available.append((path, record, sha))
            except (ValueError, KeyError, TypeError, OSError) as exc:
                print(f'Skipped {path.name}: {exc}')
        if not available:
            raise ValueError('No valid batch records found; use start first')
        path, record, sha = available[choose('Select batch', [label(r) for _, r, _ in available])]
    print(label(record))
    action = choose('Next action', ['Add measurement', 'Record / replace actual yield', 'Show report', 'Classify legacy record'])
    if action == 2:
        print(json.dumps(report(record), ensure_ascii=False, indent=2))
        return
    changed = copy.deepcopy(record)
    if action == 3:
        if record.get('record_kind') in ('real', 'test'):
            raise ValueError('Record is already classified; classification is fixed in this workflow')
        changed['record_kind'] = ('test', 'real')[choose('Classify this legacy record', ['TEST', 'REAL'])]
    elif action == 0:
        measurement(changed)
    else:
        actual_yield(changed)
    confirmed(changed)
    safe_save(path, sha, changed)
    print('Saved:', path)
    print('Previous version retained in .history. Resume for the next observation. No API requests.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('start')
    continued = sub.add_parser('resume')
    continued.add_argument('--record')
    args = parser.parse_args(argv)
    try:
        if args.command == 'start':
            start(Path.cwd())
        else:
            resume(Path.cwd(), args.record)
        return 0
    except (Cancelled, EOFError, KeyboardInterrupt):
        print('Cancelled. No changes saved by this operation.')
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Recording stopped:', exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
