import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID
import pytest
from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.myspeidel_import_builder import make_template, build_import_draft, inspect_create_contract
ROOT = Path(__file__).resolve().parents[1]
@pytest.fixture
def inputs():
    r = load_recipe(ROOT / 'recipes/lebkuchen-zauber/recipe.yaml')
    s = json.loads((ROOT / 'examples/myspeidel-import-settings.json').read_text())
    names = {'water_types': [s['water_name']], 'malts': [x['name'] for x in r['fermentables']], 'hops': ['Goldings pellets'], 'ingredients': list(s['timing_by_ingredient']), 'yeasts': [r['yeast']['name']]}
    refs = {}; n = 1
    for k, values in names.items():
        refs[k] = {}
        for name in values:
            uid = str(UUID(int=n)); n += 1
            refs[k][uid] = {'uuid': uid, 'name': name, 'owner_uuid': 'private'}
    return r, make_template({'references': refs, 'uuid': 'source'}), s

def test_mapping(inputs):
    before = deepcopy(inputs)
    d, report = build_import_draft(*inputs)
    assert inputs == before
    assert [x['duration'] for x in d['boil']['steps']] == [60,10,0]
    assert d['mashing']['adds']['malts'][0]['amount'] == 2.8
    assert d['fermentation']['adds']['yeasts'][0]['amount'] == 11.5
    assert len(d['boil']['steps'][2]['adds']['ingredients']) == 5
    assert d['boil']['steps'][1]['adds']['ingredients'][0]['amount'] == 250
    assert d['boil']['steps'][2]['adds']['ingredients'][0]['hopping_step_number'] == 3
    assert 'uuid' not in d and 'owner' not in d and 'bitterness' not in d
    assert not report['upload_ready']
    assert report['unmapped']['spice_contact_after_flameout_min'] == 5
    assert all(set(x)=={'uuid','name'} for rows in inputs[1]['references'].values() for x in rows)

@pytest.mark.parametrize('failure', ['missing','ambiguous','null_name','uuid','timing','nan','color','incomplete'])
def test_rejections(inputs,failure):
    r,t,s=inputs
    if failure=='missing':t['references']['ingredients']=[]
    if failure=='ambiguous':t['references']['hops']*=2
    if failure=='null_name':t['references']['hops'][0]['name']=None
    if failure=='uuid':t['references']['hops'][0]['uuid']='invalid'
    if failure=='timing':s['timing_by_ingredient']['Mild honey']=61
    if failure=='nan':s['wort_volume_l']=float('nan')
    if failure=='color':s['malt_colors_ebc']={}
    if failure=='incomplete':s['timing_by_ingredient'].pop('Nutmeg')
    with pytest.raises(ValueError):build_import_draft(r,t,s)

def test_other_recipe(inputs):
    r,t,s=inputs;r['recipe']['name']='Independent ale';r['fermentables'][0]['amount_g']=1234
    d,_=build_import_draft(r,t,s)
    assert d['name']=='Independent ale'
    assert d['mashing']['adds']['malts'][0]['amount']==1.234

def test_contract():
    spec={'paths':{'/v1.0/recipe':{'post':{'parameters':[{'name':'dryRun','in':'query'}],'requestBody':{'content':{'application/json':{'schema':{'type':'object','required':['uuid']}}}}}}}}
    report=inspect_create_contract(spec,{})
    assert report['dry_run_documented'] and report['schema_errors']
    assert not report['live_create_verified']
