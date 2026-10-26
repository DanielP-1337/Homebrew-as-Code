import copy
import json
from pathlib import Path
import pytest
from homebrew_as_code.brew_plan import load_brew_plan
from homebrew_as_code.brew_day import new_record, validate, report, year_summary, main

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def record():
    bundle = load_brew_plan(ROOT / 'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    return new_record(bundle, '2026-10-26')


def row(stage='pre_boil_after_adjustment', value=12):
    return {'stage': stage, 'measured_at': '2026-10-26T12:00:00+01:00',
            'instrument': '7-14 Plato hydrometer', 'raw_plato': value,
            'corrected_plato': value, 'sample_temperature_c': 20,
            'correction_method': 'At instrument reference temperature',
            'volume_l': 23, 'volume_temperature_c': 20}


def test_new_record_has_no_invented_measurements(record):
    assert validate(record)['measurements'] == []
    assert record['actual_yield']['produced_beer_l'] is None
    assert report(record)['alcohol_abv_percent'] is None


def test_stages_and_targets_are_not_conflated(record):
    record['measurements'] = [row(), row('post_boil', 13.5), row('fermentation', 3)]
    before = copy.deepcopy(record)
    result = report(record)
    assert result['measurements_by_stage']['post_boil'][0]['corrected_plato'] == 13.5
    assert result['measurements_by_stage']['fermentation'][0]['corrected_plato'] == 3
    assert record == before
    assert result['efficiency_percent'] is None


@pytest.mark.parametrize('field,value', [('raw_plato',float('nan')), ('volume_l',float('inf')),
                                         ('raw_plato',True), ('volume_l',-1), ('raw_plato',-1)])
def test_invalid_numbers(record, field, value):
    record['measurements'] = [row()]
    record['measurements'][0][field] = value
    with pytest.raises(ValueError): validate(record)


@pytest.mark.parametrize('field', ['sample_temperature_c', 'volume_temperature_c', 'correction_method'])
def test_measurement_context_required(record, field):
    record['measurements'] = [row()]
    record['measurements'][0][field] = None
    with pytest.raises(ValueError): validate(record)


def test_negative_apparent_extract_allowed(record):
    record['measurements'] = [row('fermentation', -0.5)]
    validate(record)


def test_duplicate_measurement_rejected(record):
    record['measurements'] = [row(), row()]
    with pytest.raises(ValueError): validate(record)


@pytest.mark.parametrize('stamp', ['2026-10-26T12:00:00', '2026-10-25T12:00:00+01:00'])
def test_timestamp_context(record, stamp):
    record['measurements'] = [row()]
    record['measurements'][0]['measured_at'] = stamp
    with pytest.raises(ValueError): validate(record)


def test_annual_actuals_not_wort_or_packaged_totals(record):
    record['measurements'] = [row()]
    record['actual_yield'].update(produced_beer_l=20, packaged_beer_l=18, production_date='2026-11-01')
    result = year_summary([record], 2026)
    assert result['known_produced_beer_l'] == 20
    assert result['unresolved_batches'] == []
    assert year_summary([record], 2027)['known_produced_beer_l'] == 0


def test_unknown_is_not_zero(record):
    result = year_summary([record], 2026)
    assert result['unresolved_batches'] == [record['batch_id']]
    assert result['included_batches'] == []


def test_duplicate_batch_rejected(record):
    with pytest.raises(ValueError, match='Duplicate batch_id'):
        year_summary([record, copy.deepcopy(record)], 2026)


def test_actual_requires_date_and_consistent_packaging(record):
    record['actual_yield']['produced_beer_l'] = 20
    with pytest.raises(ValueError): validate(record)
    record['actual_yield'].update(production_date='2026-11-01', packaged_beer_l=21)
    with pytest.raises(ValueError): validate(record)


def test_production_year_is_explicit(record):
    record['actual_yield'].update(produced_beer_l=20, production_date='2027-01-01')
    assert year_summary([record], 2026)['known_produced_beer_l'] == 0
    assert year_summary([record], 2027)['known_produced_beer_l'] == 20


def test_cli_report_and_bad_input(record, tmp_path, capsys):
    path = tmp_path / 'record.json'
    path.write_text(json.dumps(record), encoding='utf-8')
    assert main(['report', '--record', str(path)]) == 0
    assert 'upload_ready' in capsys.readouterr().out
    path.write_text('{}', encoding='utf-8')
    assert main(['report', '--record', str(path)]) == 2


def test_init_is_exclusive_and_does_not_change_plan(tmp_path, monkeypatch):
    import shutil
    for name in ('recipes', 'equipment', 'brew-plans'):
        shutil.copytree(ROOT / name, tmp_path / name)
    monkeypatch.chdir(tmp_path)
    plan = tmp_path / 'brew-plans/weizen-nikolaus-brew-001.yaml'
    before = plan.read_bytes()
    args = ['init', '--date', '2026-10-26', '--output', '.local/brew-days/test.json']
    assert main(args) == 0
    assert main(args) == 2
    assert plan.read_bytes() == before
    assert json.loads((tmp_path / '.local/brew-days/test.json').read_text())['measurements'] == []
