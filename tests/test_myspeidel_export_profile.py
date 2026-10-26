from copy import deepcopy
import json
from pathlib import Path
from uuid import UUID
import pytest
from homebrew_as_code.brew_plan import load_brew_plan
from homebrew_as_code.recipe_completeness import assess
from homebrew_as_code.myspeidel_export_profile import export_recipe
from homebrew_as_code.myspeidel_guided_import import needed, resolve_mapping, draft_with_mapping, MAP_FORMAT
from homebrew_as_code.myspeidel_create_candidate import additions, policy_from_backup, build_candidate, TOP
from homebrew_as_code.myspeidel_create_dry_run import validate
from homebrew_as_code.myspeidel_put_roundtrip import digest

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def setup():
    loaded = load_brew_plan(ROOT/'brew-plans/weizen-nikolaus-brew-001.yaml', repo_root=ROOT)
    settings = json.loads((ROOT/'examples/myspeidel-weizen-import-settings.json').read_text())
    return loaded, settings


def test_confirmed_profile_resolves_blockers_without_mutation(setup):
    loaded, settings = setup
    before = deepcopy(loaded)
    assert assess(loaded['recipe'], settings)['myspeidel_mapping_blockers'] == []
    recipe, fermentation, maturation, profile = export_recipe(loaded['recipe'], settings)
    assert recipe['targets']['original_gravity_plato'] == 12
    assert recipe['boil']['temperature_c'] == 101
    assert fermentation == [{'sorting':0,'temperature':22,'duration':168,'time':0}]
    assert maturation == [{'sorting':0,'temperature':7,'duration':21,'pressure':1.6}]
    assert loaded == before
    assert loaded['recipe']['fermentation']['ambient_temperature_c'] == 21.5
    assert loaded['recipe']['targets']['packaged_volume_l'] is None


@pytest.mark.parametrize('key,value', [('recipe_id','wrong'),('recipe_version','99'),
    ('original_gravity_plato',float('nan')),('original_gravity_plato',True),
    ('boil_controller_temperature_c',111),('fermentation_steps',{}),('maturation_steps',None)])
def test_invalid_profiles(setup, key, value):
    loaded, settings = setup
    settings['export_profile'][key] = value
    with pytest.raises(ValueError): export_recipe(loaded['recipe'], settings)


@pytest.mark.parametrize('kind,field,value', [
    ('fermentation_steps','duration_hours',0), ('fermentation_steps','temperature_c',float('inf')),
    ('maturation_steps','pressure_bar',-1), ('maturation_steps','duration_days',True)])
def test_invalid_steps(setup, kind, field, value):
    loaded, settings = setup
    settings['export_profile'][kind][0][field] = value
    with pytest.raises(ValueError): export_recipe(loaded['recipe'], settings)


def test_no_ambiguous_units_or_inherited_identity(setup):
    loaded, settings = setup
    step = settings['export_profile']['fermentation_steps'][0]
    step['duration'] = step.pop('duration_hours')
    with pytest.raises(ValueError): export_recipe(loaded['recipe'], settings)
    step['duration_hours'] = step.pop('duration')
    step['uuid'] = str(UUID(int=99))
    with pytest.raises(ValueError): export_recipe(loaded['recipe'], settings)


def test_full_adapter_keeps_aliases_alpha_and_fresh_process_ids(setup):
    loaded, settings = setup
    aliases = {'Münchener Leitungswasser':'Leitungswasser mittelhart', 'Weizen':'Weizen Malz',
               'Pilsner':'Pilsener', 'Zymoferm GERMAN WHEAT':'GERMAN WHEAT Trockenhefe og'}
    refs = {}; n = 1
    for kind, names in needed(loaded['recipe'],settings).items():
        refs[kind] = {}
        for name in names:
            uid = str(UUID(int=n)); n += 1
            refs[kind][uid] = {'uuid':uid,'name':aliases.get(name,name),'deleted':0,'color':None,'acid':9}
    source = {k:'' for k in TOP}
    source.update(uuid=str(UUID(int=100)), owner={'uuid':str(UUID(int=101))}, machine_type={'size':20},
                  references=refs, mashing={'adds':{'malts':[]}},boil={'steps':[]},
                  fermentation={'adds':{'yeasts':[]},'steps':[{'uuid':str(UUID(int=102))}]},
                  maturation={'steps':[{'uuid':str(UUID(int=103))}]})
    reg = {'format':MAP_FORMAT,'accounts':{}}
    template, _, decisions = resolve_mapping(loaded['recipe'],settings,source,reg,
        input_fn=lambda _:'1', output_fn=lambda _:None)
    # Select actual intended alias for Pilsner/Weizen, regardless of sorted menu order.
    for kind, names in needed(loaded['recipe'],settings).items():
        template['references'][kind] = []
        for name in names:
            match = next(r for r in refs[kind].values() if r['name']==aliases.get(name,name))
            template['references'][kind].append({'uuid':match['uuid'],'name':name})
    spec={'paths':{'/v1.0/recipe':{'post':{'parameters':[{'name':'dryRun','in':'query'}],
          'requestBody':{'content':{'application/json':{'schema':{'type':'object'}}}}}}}}
    draft = draft_with_mapping(loaded,settings,source,template,decisions,spec)
    policy = policy_from_backup(source); policy.update(assumptions_accepted=True,yeast_time='Hauptgärung')
    before = deepcopy((loaded,source,draft,policy))
    artifact = build_candidate(draft,source,policy,spec)
    c=artifact['candidate']
    assert (loaded,source,draft,policy)==before
    assert [r['color'] for r in c['mashing']['adds']['malts']]==[4,15,2]
    assert c['name']=='Weizen Nikolaus - HBAC API'
    assert loaded['recipe']['recipe']['name']=='Weizen Nikolaus'
    assert c['water_recast']==20 and c['water_plato']==12
    assert c['boil']['boiling_temperature']==101
    assert c['boil']['steps'][1]['adds']['hops'][0]['acid']==5.2
    assert c['fermentation']['steps'][0]['duration']==168
    assert c['maturation']['steps'][0]['duration']==21
    assert c['fermentation']['adds']['yeasts'][0]['time']=='Hauptgärung'
    assert c['references']==refs
    fresh={r['uuid'] for r in additions(c)}
    assert len(fresh)==8  # three malts, two hops, yeast, fermentation, maturation
    assert not fresh.intersection(r['uuid'] for r in additions(source))
    assert all(UUID(uid).version==4 for uid in fresh)
    validate(artifact,source,spec)
    # Process identities must be included in preflight collision checks too.
    c['maturation']['steps'][0]['uuid']=source['maturation']['steps'][0]['uuid']
    artifact['report']['candidate_sha256']=digest(c)
    with pytest.raises(ValueError,match='new and unique'):validate(artifact,source,spec)
