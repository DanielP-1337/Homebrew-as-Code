import copy
import json
from pathlib import Path
import pytest
from homebrew_as_code.brew_day import new_record, year_summary, validate
from homebrew_as_code.brew_plan import load_brew_plan
from homebrew_as_code import guided_brew_day as gui

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def local(tmp_path, monkeypatch):
    bundle = load_brew_plan(ROOT / 'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    record = new_record(bundle, '2026-10-26', record_kind='test')
    monkeypatch.chdir(tmp_path)
    path = tmp_path / '.local/brew-days/test.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding='utf-8')
    return path, record


def answers(monkeypatch, values):
    iterator = iter(values)
    monkeypatch.setattr('builtins.input', lambda _: next(iterator))


def test_test_records_excluded_even_with_actuals(local):
    _, record = local
    record['actual_yield'].update(produced_beer_l=500, production_date='2026-11-01')
    result = year_summary([record], 2026)
    assert result['known_produced_beer_l'] == 0
    assert result['excluded_test_batches'] == [record['batch_id']]
    assert result['unresolved_batches'] == []


def test_legacy_not_silently_assumed_real(local):
    _, record = local
    del record['record_kind']
    record['actual_yield'].update(produced_beer_l=20, production_date='2026-11-01')
    result = year_summary([record], 2026)
    assert result['known_produced_beer_l'] == 0
    assert result['unclassified_batches'] == [record['batch_id']]


def test_real_and_test_mixed(local):
    _, record = local
    actual = copy.deepcopy(record)
    actual.update(batch_id='real-batch', record_kind='real')
    actual['actual_yield'].update(produced_beer_l=19, production_date='2026-11-01')
    assert year_summary([record, actual], 2026)['known_produced_beer_l'] == 19


def test_invalid_classification(local):
    _, record = local
    record['record_kind'] = 'maybe'
    with pytest.raises(ValueError): validate(record)


def test_atomic_save_preserves_old_bytes(local):
    path, _ = local
    old = path.read_bytes()
    record, sha = gui.read_record(path)
    record['notes'] = 'new observation'
    gui.safe_save(path, sha, record)
    assert json.loads(path.read_text())['notes'] == 'new observation'
    backups = list((path.parent / '.history').rglob('*.json'))
    assert len(backups) == 1 and backups[0].read_bytes() == old
    assert not path.with_suffix('.json.lock').exists()


def test_conflict_does_not_overwrite_or_leave_lock(local):
    path, _ = local
    record, sha = gui.read_record(path)
    path.write_text(path.read_text() + '\n')
    current = path.read_bytes()
    with pytest.raises(ValueError, match='changed since'):
        gui.safe_save(path, sha, record)
    assert path.read_bytes() == current
    assert not path.with_suffix('.json.lock').exists()


def test_existing_lock_is_not_removed(local):
    path, _ = local
    record, sha = gui.read_record(path)
    lock = path.with_suffix('.json.lock')
    lock.write_text('another writer')
    with pytest.raises(ValueError, match='locked'): gui.safe_save(path, sha, record)
    assert lock.read_text() == 'another writer'


@pytest.mark.parametrize('field,value', [('batch_id','other'), ('recipe_version','9'), ('record_kind','real')])
def test_identity_and_classification_fixed(local, field, value):
    path, _ = local
    record, sha = gui.read_record(path)
    old = path.read_bytes()
    record[field] = value
    with pytest.raises(ValueError): gui.safe_save(path, sha, record)
    assert path.read_bytes() == old
    assert not path.with_suffix('.json.lock').exists()


def test_failed_replace_keeps_record_and_backup(local, monkeypatch):
    path, _ = local
    record, sha = gui.read_record(path)
    old = path.read_bytes()
    def fail(*_): raise OSError('simulated disk failure')
    monkeypatch.setattr(gui.os, 'replace', fail)
    with pytest.raises(OSError): gui.safe_save(path, sha, record)
    assert path.read_bytes() == old
    assert len(list((path.parent / '.history').rglob('*.json'))) == 1
    assert not list(path.parent.glob('*.tmp'))
    assert not path.with_suffix('.json.lock').exists()


def test_resume_cancel_leaves_bytes_unchanged(local, monkeypatch):
    path, _ = local
    old = path.read_bytes()
    answers(monkeypatch, [''])
    assert gui.main(['resume', '--record', str(path)]) == 0
    assert path.read_bytes() == old


def test_show_report_no_write(local, monkeypatch, capsys):
    path, _ = local
    old = path.read_bytes()
    answers(monkeypatch, ['3'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    output = capsys.readouterr().out
    assert 'Weizen Nikolaus' in output and 'TEST' in output
    assert path.read_bytes() == old


def test_record_yield_with_decimal_comma(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['2', '19,5', '18', '2026-11-01', 'Measured after fermentation', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    saved = json.loads(path.read_text())
    assert saved['actual_yield']['produced_beer_l'] == 19.5
    assert year_summary([saved], 2026)['known_produced_beer_l'] == 0


def test_cancel_confirmation_discards_yield(local, monkeypatch):
    path, _ = local
    old = path.read_bytes()
    answers(monkeypatch, ['2', '19', '18', '2026-11-01', '', 'no'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    assert path.read_bytes() == old


def test_add_measurement(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['1', '2', '2026-10-26T12:00:00+01:00', '7-14 Plato',
                          '12', '20', '12', 'At 20 C', '', 'After adjustment', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    saved = json.loads(path.read_text())
    assert len(saved['measurements']) == 1
    assert saved['measurements'][0]['stage'] == 'pre_boil_after_adjustment'
    assert saved['measurements'][0]['volume_l'] is None


def test_invalid_timestamp_then_cancel_never_written(local, monkeypatch):
    path, _ = local
    old = path.read_bytes()
    answers(monkeypatch, ['1', '1', 'invalid-time', 'cancel'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    assert path.read_bytes() == old


def test_legacy_explicit_classification(local, monkeypatch):
    path, record = local
    del record['record_kind']
    path.write_text(json.dumps(record))
    answers(monkeypatch, ['4', '1', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    assert json.loads(path.read_text())['record_kind'] == 'test'


def test_start_clear_selection_and_no_default_kind(tmp_path, monkeypatch, capsys):
    bundle = load_brew_plan(ROOT / 'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(gui, 'plans', lambda root: [(ROOT, bundle)])
    answers(monkeypatch, ['1', '1', '2026-10-26', 'yes'])
    assert gui.main(['start']) == 0
    paths = list((tmp_path / '.local/brew-days').glob('*.json'))
    assert len(paths) == 1
    assert json.loads(paths[0].read_text())['record_kind'] == 'test'
    assert 'Weizen Nikolaus' in capsys.readouterr().out


def test_cancel_start_does_not_create_record(tmp_path, monkeypatch):
    bundle = load_brew_plan(ROOT / 'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(gui, 'plans', lambda root: [(ROOT, bundle)])
    answers(monkeypatch, ['1', ''])
    assert gui.main(['start']) == 0
    assert not (tmp_path / '.local').exists()


def test_numeric_reprompts_invalid_and_accepts_unknown(monkeypatch):
    answers(monkeypatch, ['nan', 'wrong', '12,5', ''])
    assert gui.numeric('Number') == 12.5
    assert gui.numeric('Unknown') is None


def test_paths_outside_local_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError): gui.atomic_save(tmp_path / 'outside.json', '', {})


def test_low_level_init_defaults_to_test(tmp_path, monkeypatch):
    from homebrew_as_code import brew_day
    bundle = load_brew_plan(ROOT / 'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(brew_day, 'load_brew_plan', lambda *a, **k: bundle)
    assert brew_day.main(['init', '--date', '2026-10-26', '--output', '.local/brew-days/new.json']) == 0
    saved = json.loads((tmp_path / '.local/brew-days/new.json').read_text())
    assert saved['record_kind'] == 'test'
    assert year_summary([saved], 2026)['excluded_test_batches'] == [saved['batch_id']]


def test_immediate_validation_preserves_previous_fields(local, monkeypatch, capsys):
    path, _ = local
    answers(monkeypatch, [
        '1', '2', '2', '2026-10-26T12:00:00', '2026-10-25T12:00:00+01:00',
        '2026-10-26T12:00:00+01:00', 'Keep this instrument',
        '-1', '12', '', '120', '20', '41', '12', '', 'At reference temperature',
        '-2', '23', '', '120', '20', 'Keep this note', 'yes',
    ])
    assert gui.main(['resume', '--record', str(path)]) == 0
    saved = json.loads(path.read_text())['measurements'][0]
    assert saved['instrument'] == 'Keep this instrument'
    assert saved['raw_plato'] == saved['corrected_plato'] == 12
    assert saved['sample_temperature_c'] == saved['volume_temperature_c'] == 20
    assert saved['volume_l'] == 23
    assert saved['note'] == 'Keep this note'
    output = capsys.readouterr().out
    assert 'Include a timezone offset' in output
    assert 'cannot precede brew date' in output


def test_duplicate_instant_reprompt(local, monkeypatch):
    _, record = local
    record['measurements'] = [{'stage': 'post_boil', 'measured_at': '2026-10-26T12:00:00+01:00'}]
    answers(monkeypatch, ['2026-10-26T11:00:00+00:00', '2026-10-26T12:01:00+01:00'])
    assert gui.measured_at(record, 'post_boil') == '2026-10-26T12:01:00+01:00'


def test_yield_reprompts_without_losing_produced(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['2', '-1', '20', '21', '19', '2026-10-25', '2026-10-26', 'Simulated', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    actual = json.loads(path.read_text())['actual_yield']
    assert actual['produced_beer_l'] == 20
    assert actual['packaged_beer_l'] == 19
    assert actual['production_date'] == '2026-10-26'


def test_corrected_only_requires_sample_temperature(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['1', '3', '2026-10-26T12:00:00+01:00', 'Hydrometer',
                          '', '', '12', '', '20', 'Instrument scale', '', '', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    row = json.loads(path.read_text())['measurements'][0]
    assert row['raw_plato'] is None
    assert row['corrected_plato'] == 12
    assert row['sample_temperature_c'] == 20


def test_volume_only_requires_a_value_and_volume_temperature(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['1', '3', '2026-10-26T12:00:00+01:00', 'Vessel scale',
                          '', '', '', '', '20', '', '20', '', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    row = json.loads(path.read_text())['measurements'][0]
    assert row['raw_plato'] is row['corrected_plato'] is None
    assert row['volume_l'] == 20
    assert row['volume_temperature_c'] == 20


def test_negative_fermentation_reading_still_allowed(local, monkeypatch):
    path, _ = local
    answers(monkeypatch, ['1', '4', '2026-10-26T12:00:00+01:00', 'Hydrometer',
                          '-0,5', '20', '', '', '', 'yes'])
    assert gui.main(['resume', '--record', str(path)]) == 0
    assert json.loads(path.read_text())['measurements'][0]['raw_plato'] == -0.5


def test_zero_packaged_bound_and_cancel_after_bad_number(monkeypatch):
    answers(monkeypatch, ['1', '0'])
    assert gui.numeric('Packaged', minimum=0, maximum=0) == 0
    answers(monkeypatch, ['-1', 'cancel'])
    with pytest.raises(gui.Cancelled): gui.numeric('Volume', minimum=0)
