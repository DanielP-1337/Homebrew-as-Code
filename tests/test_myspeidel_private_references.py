from copy import deepcopy
import pytest
from homebrew_as_code.recipe import load_recipe
from homebrew_as_code.myspeidel_private_references import extract_observations, confirm_observations
from homebrew_as_code.myspeidel_catalog_resolver import resolve_snapshot

UID1 = '123e4567-e89b-42d3-a456-426614174000'
UID2 = '123e4567-e89b-42d3-a456-426614174001'
RECIPE='recipes/lebkuchen-zauber/recipe.yaml'
SPEC={'openapi':'3.0.3','paths':{'/v1.0/recipe/{uuid}':{'get':{}}}}

def detail():
    return {'uuid':UID1,'public':0,'machine_type':{'size':20},
            'mashing':{'adds':{'malts':[{'malt_uuid':UID1}]}},
            'boil':{'steps':[{'adds':{'hops':[{'hop_uuid':UID2}]}}]}}

def test_observed_identifiers_without_names():
    x=extract_observations(detail())
    assert len(x['observations'])==2 and x['confirmed'] is False
    assert x['observations'][0]['observed_kind']=='malt'
    assert x['observations'][1]['observed_kind']=='hop'
    assert 'name' not in x['observations'][0]

def test_reject_wrong_equipment_or_bad_uuid():
    x=detail();x['machine_type']['size']=50
    with pytest.raises(ValueError):extract_observations(x)
    x=detail();x['mashing']['adds']['malts'][0]['malt_uuid']='invalid'
    with pytest.raises(ValueError):extract_observations(x)

def test_explicit_confirmation_compatible_with_resolver():
    observed=extract_observations(detail())
    decisions={'confirmations':[{'observation_index':0,'kind':'malt','name':'Pale Ale Malt','web_verified':True},
                                {'observation_index':1,'kind':'hop','name':'Goldings pellets','web_verified':True}]}
    snapshot=confirm_observations(load_recipe(RECIPE),observed,decisions)
    result=resolve_snapshot(load_recipe(RECIPE),SPEC,snapshot)
    assert result['resolved_count']==2
    assert result['upload_ready'] is False

def test_unconfirmed_or_wrong_name_blocked():
    observed=extract_observations(detail())
    for selection in [{'observation_index':0,'kind':'malt','name':'Pale Ale Malt','web_verified':False},
                      {'observation_index':0,'kind':'malt','name':'Wrong','web_verified':True}]:
        with pytest.raises(ValueError): confirm_observations(load_recipe(RECIPE),observed,{'confirmations':[selection]})

def test_duplicate_selection_blocked():
    observed=extract_observations(detail())
    d={'observation_index':0,'kind':'malt','name':'Pale Ale Malt','web_verified':True}
    with pytest.raises(ValueError):confirm_observations(load_recipe(RECIPE),observed,{'confirmations':[d,d]})

def test_unconfirmed_recipe_provenance_rejected():
    observed=extract_observations(detail())
    x=confirm_observations(load_recipe(RECIPE),observed,{'confirmations':[{'observation_index':0,'kind':'malt','name':'Pale Ale Malt','web_verified':True}]})
    x['entries'][0]['web_verified']=False
    with pytest.raises(ValueError):resolve_snapshot(load_recipe(RECIPE),SPEC,x)
