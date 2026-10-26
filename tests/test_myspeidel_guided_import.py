from copy import deepcopy
import json
from pathlib import Path
from uuid import UUID
import pytest
from homebrew_as_code.myspeidel_guided_import import (
    resolve_mapping, draft_with_mapping, normal, choose, atomic_json, locked,
    FORMAT, MAP_FORMAT, read_session, actions, candidate_artifact, perform, start)
from homebrew_as_code.myspeidel_put_roundtrip import digest,write_new
from homebrew_as_code.brew_plan import load_brew_plan

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def inputs():
    loaded=load_brew_plan(ROOT/'brew-plans/lebkuchen-zauber-brew-001.yaml',repo_root=ROOT)
    settings=json.loads((ROOT/'examples/myspeidel-import-settings.json').read_text())
    from homebrew_as_code.myspeidel_guided_import import needed
    refs={};index=1
    for kind,names in needed(loaded['recipe'],settings).items():
        refs[kind]={}
        for name in names:
            uid=str(UUID(int=index));index+=1
            refs[kind][uid]={'uuid':uid,'name':name,'deleted':0}
    source={'owner':{'uuid':'account-one'},'references':refs}
    return loaded,settings,source,{'format':MAP_FORMAT,'accounts':{}}


def test_mapping_reuses_account_scoped_ids(inputs):
    loaded,settings,source,reg=inputs;before=deepcopy(inputs)
    t,r,d=resolve_mapping(loaded['recipe'],settings,source,reg)
    assert inputs==before and len(d)==14
    assert all(x['selection']=='exact_name' for x in d)
    _,r2,d2=resolve_mapping(loaded['recipe'],settings,source,r)
    assert r2==r and all(x['selection']=='saved' for x in d2)
    source['owner']['uuid']='account-two'
    _,_,d3=resolve_mapping(loaded['recipe'],settings,source,r)
    assert all(x['selection']=='exact_name' for x in d3)


def test_alias_explicit_and_remote_name_preserved(inputs):
    loaded,settings,source,reg=inputs
    row=next(iter(source['references']['hops'].values()));row['name']='East Kent Goldings'
    out=[]
    template,updated,decisions=resolve_mapping(loaded['recipe'],settings,source,reg,lambda _: '1',out.append)
    assert any('East Kent Goldings' in x for x in out)
    draft=draft_with_mapping(loaded,settings,source,template,decisions,None)
    assert next(iter(draft['candidate']['references']['hops'].values()))['name']=='East Kent Goldings'
    assert draft['candidate']['boil']['steps'][0]['adds']['hops'][0]['hop_uuid']==row['uuid']
    assert digest(draft['candidate'])==draft['report']['candidate_sha256']
    assert any(x['selection']=='explicit_selection' for x in decisions)


@pytest.mark.parametrize('change',['renamed','removed','deleted'])
def test_stale_mapping_requires_selection(inputs,change):
    loaded,settings,source,reg=inputs
    _,reg,_=resolve_mapping(loaded['recipe'],settings,source,reg)
    kind='malts';uid=next(iter(source['references'][kind]));row=source['references'][kind][uid]
    if change=='renamed':row['name']='Renamed malt'
    if change=='removed':del source['references'][kind][uid]
    if change=='deleted':row['deleted']=1
    with pytest.raises(ValueError,match='Cancelled'):
        resolve_mapping(loaded['recipe'],settings,source,reg,lambda _: '')


def test_duplicate_names_require_clear_choice(inputs):
    loaded,settings,source,reg=inputs
    row=next(iter(source['references']['hops'].values()));uid=str(UUID(int=999))
    source['references']['hops'][uid]={**row,'uuid':uid}
    out=[]
    t,r,d=resolve_mapping(loaded['recipe'],settings,source,reg,lambda _:'2',out.append)
    assert any(uid in x for x in out)
    assert next(x for x in d if x['category']=='hops')['selection']=='explicit_selection'


@pytest.mark.parametrize('answer',['','0','abc','3'])
def test_cancel_invalid_menu(answer):
    with pytest.raises(ValueError):choose('menu',[('one',1),('two',2)],lambda _:answer,lambda _:None)


def test_session_integrity_and_lock(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);folder=Path('.local/session');folder.mkdir(parents=True)
    atomic_json(folder/'backup.json',{'x':1})
    s={'format':FORMAT,'fixed':{'backup.json':digest({'x':1})},'frozen':{}}
    atomic_json(folder/'session.json',s)
    assert read_session(folder)==s
    with locked(folder/'lock'):
        with pytest.raises(ValueError):
            with locked(folder/'lock'):pass
    assert not (folder/'lock').exists()
    atomic_json(folder/'backup.json',{'x':2})
    with pytest.raises(ValueError):read_session(folder)


def test_interrupted_preparation_preserves_candidate(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);folder=Path('.local/session');folder.mkdir(parents=True)
    atomic_json(folder/'settings.json',{'water':'RO'})
    atomic_json(folder/'prepared-inputs.json',{'settings.json':digest({'water':'RO'})})
    atomic_json(folder/'candidate.json',{'uuid':'original'})
    s={'frozen':{}}
    assert candidate_artifact(folder,s)=={'uuid':'original'}
    assert s['frozen']['candidate.json']==digest({'uuid':'original'})


def test_network_action_records_intent_and_propagates_failure(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);folder=Path('.local/session');folder.mkdir(parents=True)
    s={'dry_runs':[],'live_runs':[]}
    import homebrew_as_code.myspeidel_create_dry_run as dry
    def child(argv):
        stored=json.loads((folder/'session.json').read_text())
        assert len(stored['dry_runs'])==1
        assert '--candidate' in argv and '--diagnostics' in argv
        return 2
    monkeypatch.setattr(dry,'main',child)
    assert perform(folder,s,'dry')==2
    assert len(s['dry_runs'])==1


def test_no_candidate_only_offers_offline_preparation(tmp_path):
    assert actions(tmp_path,{'frozen':{}})==[('Prepare candidate (offline)','prepare')]


@pytest.mark.parametrize('receipt,attempted,expected',[(False,False,'dry'),(True,False,'create'),(True,True,'verify')])
def test_resume_action_gates(tmp_path,monkeypatch,receipt,attempted,expected):
    import homebrew_as_code.myspeidel_guided_import as g
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(g,'candidate_artifact',lambda *a:{'candidate':{'uuid':str(UUID(int=8))}})
    monkeypatch.setattr(g,'read_backup',lambda *a:(None,{},None))
    monkeypatch.setattr(g,'read_json',lambda *a:{})
    monkeypatch.setattr(g,'validate',lambda *a:({'uuid':str(UUID(int=8))},{}))
    monkeypatch.setattr(g,'latest_receipt',lambda *a:Path('receipt') if receipt else None)
    state={'live_runs':['unknown.json'] if attempted else []}
    assert g.actions(tmp_path,state)[0][1]==expected


def test_cancelled_live_child_can_be_resumed(tmp_path,monkeypatch):
    import homebrew_as_code.myspeidel_guided_import as g
    import homebrew_as_code.myspeidel_live_create as live
    monkeypatch.chdir(tmp_path);folder=Path('.local/session');folder.mkdir(parents=True)
    monkeypatch.setattr(g,'read_backup',lambda *a:(None,{},None))
    monkeypatch.setattr(g,'read_json',lambda *a:{'candidate':{}})
    monkeypatch.setattr(g,'latest_receipt',lambda *a:Path('receipt'))
    monkeypatch.setattr(live,'main',lambda *a:0)
    state={'dry_runs':[],'live_runs':[]}
    assert g.perform(folder,state,'create')==0
    assert state['live_runs']==[]


def test_missing_catalog_category_cannot_invent_mapping(inputs):
    loaded,settings,source,reg=inputs
    source['references']['hops']={}
    with pytest.raises(ValueError,match='no available entries'):
        resolve_mapping(loaded['recipe'],settings,source,reg)


@pytest.mark.parametrize('verbose',[False,True])
def test_dry_run_compact_and_verbose_save_same_report(tmp_path,monkeypatch,capsys,verbose):
    import homebrew_as_code.myspeidel_create_dry_run as dry
    import homebrew_as_code.myspeidel_auth as auth
    import homebrew_as_code.myspeidel_credentials as credentials
    monkeypatch.chdir(tmp_path);Path('.local').mkdir()
    Path('.local/candidate').write_text('{}');Path('.local/backup').write_text('{}')
    c={'name':'Example','uuid':str(UUID(int=123))};s={'name':'Source'}
    monkeypatch.setattr(dry,'read_json',lambda *a:{})
    monkeypatch.setattr(dry,'read_backup',lambda *a:(None,s,None))
    monkeypatch.setattr(dry,'validate',lambda *a:(c,{'unverified_constraints':[]}))
    monkeypatch.setattr(credentials,'prompt_credentials',lambda:('user','password'))
    monkeypatch.setattr(auth,'login',lambda *a,**k:'secret-token')
    monkeypatch.setattr('builtins.input',lambda *a:'yes')
    report={'result':'DRY_RUN_VERIFIED','passed':True,'post_attempted':True,
            'post_http_status':200,'events':[{'body':'full-detail-sentinel'}]}
    monkeypatch.setattr(dry,'run',lambda *a:deepcopy(report))
    argv=['--candidate','.local/candidate','--backup','.local/backup','--spec','spec.json',
          '--diagnostics','.local/report.json']
    assert dry.main(argv+(['--verbose'] if verbose else []))==0
    output=capsys.readouterr().out
    assert ('full-detail-sentinel' in output)==verbose
    saved=json.loads(Path('.local/report.json').read_text())
    assert saved['events']==report['events']
