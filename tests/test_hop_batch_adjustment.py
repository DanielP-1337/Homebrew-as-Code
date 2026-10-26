from copy import deepcopy
from pathlib import Path
import math
import pytest
import yaml
from homebrew_as_code.hop_batch_adjustment import adjust,batch_plan,main

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('alpha,expected',[(5.2,13),(6.5,10.4),(7.1,13*5.2/7.1)])
def test_alpha_mass_preserved(alpha,expected):
    value=adjust(13,5.2,alpha)
    assert value==pytest.approx(expected)
    assert value*alpha==pytest.approx(13*5.2)

@pytest.mark.parametrize('bad',[0,-1,True,None,'6.5',float('nan'),float('inf'),101])
def test_invalid_batch_alpha(bad):
    with pytest.raises(ValueError):adjust(13,5.2,bad)

def test_confirmed_reference_separate_from_batch():
    d=yaml.safe_load((ROOT/'recipes/weizen-nikolaus/confirmed-draft.yaml').read_text(encoding='utf-8'))
    before=deepcopy(d);r=batch_plan(d,'perle-late',6.5)
    assert d==before
    assert r['batch_amount_g']==pytest.approx(10.4) and r['remaining_min']==15
    assert d['water']['filtered'] is False and d['water']['salt_additions'] is None
    assert d['fermentation']['ambient_temperature_c']==21.5
    assert d['fermentation']['measured_beer_temperature_c'] is None
    assert d['yeast']['amount_g']==7 and not r['upload_ready']

def test_missing_or_duplicate_addition():
    d={'format':'homebrew-as-code/confirmed-recipe-draft-v1','boil':{'additions':[]}}
    with pytest.raises(ValueError):batch_plan(d,'missing',6.5)
    d['boil']['additions']=[{'id':'same'},{'id':'same'}]
    with pytest.raises(ValueError):batch_plan(d,'same',6.5)

def test_cli_creates_local_adjustment(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(['--recipe',str(ROOT/'recipes/weizen-nikolaus/confirmed-draft.yaml'),
        '--batch-alpha','6.5','--output','.local/adjustment.json'])==0
    assert (tmp_path/'.local/adjustment.json').exists()
