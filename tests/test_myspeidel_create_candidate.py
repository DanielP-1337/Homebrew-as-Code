from copy import deepcopy
from uuid import UUID
import pytest
from homebrew_as_code.myspeidel_create_candidate import (
    TOP, additions, build_candidate, choose_references, policy_from_backup, main)
from homebrew_as_code.myspeidel_put_roundtrip import digest


@pytest.fixture
def inputs():
    uid = str(UUID(int=1))
    ref = {'uuid': uid, 'name': 'CaraMunich II', 'color': 90}
    candidate = {'name': 'New ale', 'public': 0, 'recipe_type': 0,
        'mashing': {'adds': {'malts': [{'malt_uuid': uid, 'amount': .45}]}},
        'boil': {'steps': []}, 'fermentation': {'adds': {'yeasts': []}},
        'references': {k: {} for k in ('water_types','malts','hops','ingredients','yeasts')}}
    candidate['references']['malts'][uid] = {'uuid':uid,'name':ref['name']}
    source = {k: '' for k in TOP}
    source.update(uuid=str(UUID(int=2)), machine_type={'size':20}, references={'malts':{uid:ref}})
    policy = policy_from_backup(source);policy['assumptions_accepted']=True
    draft = {'format':'homebrew-as-code/myspeidel-import-draft-v1','candidate':candidate,
             'report':{'candidate_sha256':digest(candidate),'unmapped':{'example':True}}}
    spec = {'paths':{'/v1.0/recipe':{'post':{'parameters':[{'name':'dryRun','in':'query'}],
        'requestBody':{'content':{'application/json':{'schema':{'oneOf':[
            {'type':'object','required':['uuid','owner']}]}}}}}}}}
    return draft, source, policy, spec


def test_new_identities_reuse_catalog_and_no_mutation(inputs):
    before=deepcopy(inputs)
    a=build_candidate(*inputs);b=build_candidate(*inputs)
    assert inputs==before
    rows=list(additions(a['candidate']))
    assert UUID(a['candidate']['uuid']).version==4
    assert UUID(rows[0]['uuid']).version==4
    assert a['candidate']['uuid']!=b['candidate']['uuid']
    assert rows[0]['uuid']!=list(additions(b['candidate']))[0]['uuid']
    assert a['candidate']['references']=={'water_types':{},'malts':inputs[1]['references']['malts'],
                                       'hops':{},'ingredients':{},'yeasts':{}}
    assert rows[0]['malt_uuid']==str(UUID(int=1))
    assert digest(a['candidate'])==a['report']['candidate_sha256']
    assert not a['report']['upload_ready']
    assert a['report']['source_report']['unmapped']=={'example':True}


@pytest.mark.parametrize('failure',['digest','policy','reference','metadata','version','equipment'])
def test_invalid_inputs(inputs,failure):
    d,s,p,_=inputs
    if failure=='digest':d['candidate']['name']='changed'
    if failure=='policy':p['assumptions_accepted']=False
    if failure=='reference':s['references']['malts']={}
    if failure=='metadata':p['recipe_fields']['uuid']='old'
    if failure=='version':p['content_version']=True
    if failure=='equipment':p['recipe_fields']['machine_type']['size']=50
    with pytest.raises(ValueError):build_candidate(*inputs)


def test_branch_diagnostics(inputs):
    spec=inputs[3]
    spec['paths']['/v1.0/recipe']['post']['requestBody']['content']['application/json']['schema']['oneOf'][0]['required'].append('missing')
    result=build_candidate(*inputs)
    assert result['report']['contract']['schema_errors'][0]['code']=='oneOf_mismatch'
    assert {'path':'$.missing','code':'required_missing'} in result['report']['branches'][0]['errors']


@pytest.mark.parametrize('answer',['2','','99'])
def test_clear_name_selection(answer):
    template={'references':{k:[] for k in ('water_types','malts','hops','ingredients','yeasts')}}
    template['references']['malts']=[{'uuid':'a','name':'CaraMunich II'}, {'uuid':'b','name':'caramunich ii'}]
    before=deepcopy(template);output=[]
    if answer=='2':
        result=choose_references(template,lambda _:answer,output.append)
        assert result['references']['malts']==[template['references']['malts'][1]]
        assert 'CaraMunich II' in output[1]
    else:
        with pytest.raises(ValueError):choose_references(template,lambda _:answer,output.append)
    assert template==before


def test_cli_rejects_missing_input_without_output(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(['policy','--backup','.local/absent.json','--output','.local/output.json'])==2
    assert not (tmp_path/'.local/output.json').exists()
