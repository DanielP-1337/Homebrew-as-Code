from copy import deepcopy
from pathlib import Path
import pytest
import yaml

from homebrew_as_code.brew_plan import BrewPlanError, load_brew_plan, load_equipment

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'brew-plans/lebkuchen-zauber-brew-001.yaml'
EQUIPMENT = ROOT / 'equipment/speidel-braumeister-20l.yaml'


def test_reference_equipment_loads():
    equipment = load_equipment(EQUIPMENT)
    assert equipment['parameters']['pre_boil_volume_l'] == 25.42
    assert equipment['reference']['verification'] == 'UNVERIFIED_EQUIPMENT_PRESET'


def test_draft_resolves_without_scaling():
    result = load_brew_plan(PLAN, repo_root=ROOT)
    assert result['recipe']['recipe']['version'] == '1.3.0'
    assert sum(m['amount_g'] for m in result['recipe']['fermentables']) == 5100
    assert result['recipe']['water']['mash_l'] == 23
    assert result['equipment']['parameters']['batch_volume_l'] == 21
    assert result['plan']['brew_plan']['intended_packaged_volume_l'] == 20
    assert len(result['warnings']) == 3


def test_missing_profile_rejected(tmp_path):
    doc = yaml.safe_load(PLAN.read_text(encoding='utf-8'))
    doc['brew_plan']['equipment_path'] = 'equipment/missing.yaml'
    p = tmp_path / 'plan.yaml'
    p.write_text(yaml.safe_dump(doc), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='not found'):
        load_brew_plan(p, repo_root=ROOT)


def test_reference_traversal_rejected(tmp_path):
    doc = yaml.safe_load(PLAN.read_text(encoding='utf-8'))
    doc['brew_plan']['equipment_path'] = '../elsewhere.yaml'
    p = tmp_path / 'plan.yaml'
    p.write_text(yaml.safe_dump(doc), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='Unsafe reference path'):
        load_brew_plan(p, repo_root=ROOT)


def test_recipe_version_mismatch_rejected(tmp_path):
    doc = yaml.safe_load(PLAN.read_text(encoding='utf-8'))
    doc['brew_plan']['recipe_version'] = '999.0'
    p = tmp_path / 'plan.yaml'
    p.write_text(yaml.safe_dump(doc), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='version mismatch'):
        load_brew_plan(p, repo_root=ROOT)


def test_equipment_id_mismatch_rejected(tmp_path):
    doc = yaml.safe_load(PLAN.read_text(encoding='utf-8'))
    doc['brew_plan']['equipment_id'] = 'other'
    p = tmp_path / 'plan.yaml'
    p.write_text(yaml.safe_dump(doc), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='ID mismatch'):
        load_brew_plan(p, repo_root=ROOT)


def test_volume_mismatch_rejected(tmp_path):
    doc = yaml.safe_load(PLAN.read_text(encoding='utf-8'))
    doc['brew_plan']['intended_packaged_volume_l'] = 21
    p = tmp_path / 'plan.yaml'
    p.write_text(yaml.safe_dump(doc), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='scaling not supported'):
        load_brew_plan(p, repo_root=ROOT)


def test_equipment_invalid_percentage(tmp_path):
    data = yaml.safe_load(EQUIPMENT.read_text(encoding='utf-8'))
    data['parameters']['brewhouse_efficiency_percent'] = 120
    p = tmp_path / 'equipment.yaml'
    p.write_text(yaml.safe_dump(data), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='percentage'):
        load_equipment(p)


def test_equipment_rejects_non_numeric(tmp_path):
    data = yaml.safe_load(EQUIPMENT.read_text(encoding='utf-8'))
    data['parameters']['lauter_deadspace_l'] = '3.5'
    p = tmp_path / 'equipment.yaml'
    p.write_text(yaml.safe_dump(data), encoding='utf-8')
    with pytest.raises(BrewPlanError, match='numeric'):
        load_equipment(p)
