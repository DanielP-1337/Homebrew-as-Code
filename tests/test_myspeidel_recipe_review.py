from copy import deepcopy
import pytest
from homebrew_as_code.myspeidel_recipe_review import review
from homebrew_as_code.myspeidel_guided_import import MAP_FORMAT

@pytest.fixture
def source():
    return {'name':'Second recipe','owner':{'uuid':'account'},'color':0,
      'mashing':{'temperature':45,'adds':{'water':{'uuid':'water','water_amount_start':20},
        'malts':[{'malt_uuid':'malt','amount':3.5,'color':0}]}},
      'rest':{'water_amount_addition':8,'steps':[{'duration':30,'temperature':62}]},
      'boil':{'boiling_duration':90,'boiling_temperature':101,'steps':[
        {'duration':15,'adds':{'hops':[{'hop_uuid':'hop','amount':13,'acid':3.2}]}}]},
      'fermentation':{'steps':[],'adds':{}},
      'references':{'water_types':{'water':{'uuid':'water','name':None}},
        'malts':{'malt':{'uuid':'malt','name':'Munich'}},
        'hops':{'hop':{'uuid':'hop','name':None,'acid':9}}}}

def test_unknowns_and_conflicts_preserved(source):
    before=deepcopy(source);r=review(source)
    assert source==before and not r['upload_ready'] and not r['canonical_recipe_created']
    codes={x['code'] for x in r['review_items']}
    assert {'missing_catalog_name','alpha_conflict','missing_yeast','water_assignment_required',
            'packaged_volume_required','recipe_color_unconfirmed'}<=codes
    hop=r['observed']['hops'][0]
    assert hop['name'] is None and hop['addition_alpha_percent']==3.2 and hop['catalog_alpha_percent']==9

@pytest.mark.parametrize('account,uid,status',[
    ('account','malt','reusable_identity'),('account','different','name_match_different_identity'),
    ('other','malt','new_mapping')])
def test_cross_recipe_identity_scoped(source,account,uid,status):
    reg={'format':MAP_FORMAT,'accounts':{account:{'malts':{'munich':{'uuid':uid,'name':'Munich'}}}}}
    r=review(source,reg)
    assert next(x for x in r['ingredient_mapping'] if x['category']=='malts')['status']==status

def test_alias_identity_reuse(source):
    reg={'format':MAP_FORMAT,'accounts':{'account':{'malts':{'alias':{'uuid':'malt','name':'Munich'}}}}}
    r=review(source,reg)
    assert next(x for x in r['ingredient_mapping'] if x['category']=='malts')['status']=='reusable_identity'

def test_missing_reference_and_deleted(source):
    source['references']['hops']={}
    source['references']['malts']['malt']['deleted']=1
    codes={x['code'] for x in review(source)['review_items']}
    assert 'missing_reference' in codes and 'deleted_reference' in codes

def test_no_fake_ready_on_complete_names(source):
    source['references']['water_types']['water']['name']='RO'
    source['references']['hops']['hop']['name']='Hop'
    assert review(source)['upload_ready'] is False
