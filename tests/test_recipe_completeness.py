from pathlib import Path
from copy import deepcopy
import pytest
import yaml
from homebrew_as_code.recipe_completeness import load_draft,validate_draft,assess
from homebrew_as_code.brew_plan import load_brew_plan,BrewPlanError
from homebrew_as_code.recipe import load_recipe,RecipeError
from homebrew_as_code.myspeidel_import_builder import build_import_draft
from homebrew_as_code.myspeidel_guided_import import plans
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def draft():return load_draft(ROOT/'recipes/weizen-nikolaus/recipe.yaml')

def test_variable_yield_promotion(draft):
    loaded=load_brew_plan(ROOT/'brew-plans/weizen-nikolaus-brew-001.yaml',repo_root=ROOT)
    assert loaded['recipe']==draft
    assert loaded['plan']['brew_plan']['intended_packaged_volume_l'] is None
    assert draft['gravity_control']['target_plato']==12
    assert draft['targets']['original_gravity_plato'] is None
    assert any('Weizen Nikolaus' in label for label,_ in plans(ROOT))

def test_optional_targets_not_export_blockers(draft):
    before=deepcopy(draft);r=assess(draft)
    assert draft==before and r['domain_valid'] and not r['upload_ready']
    assert set(r['optional_unknowns'])=={'packaged_volume_l','alcohol_abv_percent','bitterness_ibu'}
    assert not any('packaged_volume' in x for x in r['myspeidel_mapping_blockers'])
    assert r['myspeidel_mapping_blockers']

@pytest.mark.parametrize('bad',[True,float('nan'),float('inf'),-1,0])
def test_invalid_gravity(draft,bad):
    draft['gravity_control']['target_plato']=bad
    with pytest.raises(RecipeError):validate_draft(draft)

def test_fixed_yield_cannot_silently_override(draft):
    draft['targets']['packaged_volume_l']=20
    with pytest.raises(RecipeError):validate_draft(draft)

def test_legacy_stays_strict(draft):
    assert load_recipe(ROOT/'recipes/lebkuchen-zauber/recipe.yaml')['schema_version']==1
    with pytest.raises(RecipeError):load_recipe(ROOT/'recipes/weizen-nikolaus/recipe.yaml')

def test_export_fails_before_mapping(draft):
    with pytest.raises(ValueError,match='MySpeidel draft mapping needs'):
        build_import_draft(draft,{}, {})

def test_partial_export_inputs_remove_only_resolved_blockers(draft):
    draft['boil']['temperature_c']=100
    settings={'wort_volume_l':19.2,'malt_colors_ebc':{x['name']:5 for x in draft['fermentables']}}
    r=assess(draft,settings)
    assert len(r['myspeidel_mapping_blockers'])==1
    assert 'final OG' in r['myspeidel_mapping_blockers'][0]
    assert draft['fermentation']['ambient_temperature_c']==21.5

def test_v2_adapter_preserves_unknowns_and_ambient_context(draft):
    from homebrew_as_code.myspeidel_import_builder import TEMPLATE_FORMAT
    from uuid import UUID
    draft['boil']['temperature_c']=100
    draft['targets']['original_gravity_plato']=12
    names={'water_types':[draft['water']['source']], 'malts':[x['name'] for x in draft['fermentables']],
           'hops':[x['ingredient'] for x in draft['boil']['additions']], 'ingredients':[], 'yeasts':[draft['yeast']['name']]}
    n=1;refs={}
    for kind,rows in names.items():
        refs[kind]=[]
        for name in rows:
            refs[kind].append({'name':name,'uuid':str(UUID(int=n))});n+=1
    settings={'water_name':draft['water']['source'],'wort_volume_l':18.7,
              'malt_colors_ebc':{x['name']:5 for x in draft['fermentables']},'timing_by_ingredient':{}}
    c,r=build_import_draft(draft,{'format':TEMPLATE_FORMAT,'references':refs},settings)
    assert c['water_recast']==18.7
    assert r['unmapped']['target_alcohol_abv_percent'] is None
    assert r['unmapped']['fermentation_temperature_c'] is None
    assert r['unmapped']['fermentation_context']['ambient_temperature_c']==21.5
    assert r['unmapped']['packaging'] is None
    assert draft['targets']['packaged_volume_l'] is None

def test_v2_plan_cannot_claim_ready(tmp_path):
    path=ROOT/'brew-plans/weizen-nikolaus-brew-001.yaml'
    data=yaml.safe_load(path.read_text());data['brew_plan']['status']='ready'
    out=tmp_path/'plan.yaml';out.write_text(yaml.safe_dump(data))
    with pytest.raises(BrewPlanError,match='draft brew plan'):load_brew_plan(out,repo_root=ROOT)
