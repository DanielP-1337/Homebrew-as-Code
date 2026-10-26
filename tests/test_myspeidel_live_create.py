import json
from copy import deepcopy
from uuid import UUID
import pytest
from homebrew_as_code.myspeidel_live_create import run,compare,verify_receipt,BASE,POST_URL,summary
from homebrew_as_code.myspeidel_put_roundtrip import digest

@pytest.fixture
def pair():
    s={'uuid':str(UUID(int=1)),'name':'Source','public':0,'machine_type':{'size':20}}
    c={**s,'uuid':str(UUID(int=2)),'name':'Candidate','created_on':'old',
       'references':{'malts':{'catalog':{'uuid':'catalog','name':'Cara II'}}}}
    return c,s


def setup(pair,post=None,after=None):
    c,s=pair;calls=[]
    seq=[(200,{},json.dumps(s).encode()),(404,{},b'{}'),
         post if post is not None else (201,{},b'{"message":"HTTP 201 Created"}'),
         (200,{},json.dumps(s).encode()),after if after is not None else (200,{},json.dumps(c).encode())]
    def transport(req,limit):
        calls.append(req);x=seq.pop(0)
        if isinstance(x,BaseException):raise x
        return x
    return transport,calls


def test_success_and_marker_order(pair):
    transport,calls=setup(pair);marks=[]
    def guard():
        assert len(calls)==2
        marks.append(True)
    r=run('sensitive-token',*pair,transport=transport,before_send=guard)
    assert marks==[True] and r['passed']
    assert calls[2].full_url==BASE and calls[2].get_method()=='POST'
    assert json.loads(calls[2].data)==pair[0]
    assert 'sensitive-token' not in json.dumps(r)
    assert r['after_candidate']['recipe']==pair[0]


@pytest.mark.parametrize('post',[TimeoutError(),KeyboardInterrupt(),(400,{},b'{}'),(500,{},b'{}'),
    (200,{},b'{"message":"DRY RUN SUCCEEDED"}'),(201,{},b'bad'),(302,{},b'')])
def test_failure_still_gets_without_retry(pair,post):
    t,calls=setup(pair,post)
    r=run('token',*pair,transport=t,before_send=lambda:None)
    assert not r['passed'] and len(calls)==5
    assert sum(x.get_method()=='POST' for x in calls)==1
    assert r['after_candidate']['status']=='present'


def test_guard_failure_prevents_post(pair):
    t,calls=setup(pair)
    def fail():raise FileExistsError()
    # Different sequence because POST is not called.
    c,s=pair
    seq=[(200,{},json.dumps(s).encode()),(404,{},b''),(200,{},json.dumps(s).encode()),(404,{},b'')]
    calls=[]
    def transport(req,limit):calls.append(req);return seq.pop(0)
    r=run('token',*pair,transport=transport,before_send=fail)
    assert not r['post_attempted'] and all(x.get_method()=='GET' for x in calls)


def test_verify_only_after_uncertain_create(pair):
    c,s=pair;calls=[]
    def t(req,limit):
        calls.append(req)
        return 200,{},json.dumps(s if req.full_url.endswith(s['uuid']) else c).encode()
    r=run('token',*pair,transport=t,verify_only=True)
    assert r['passed'] and r['result']=='GET_COMPARISON_VERIFIED'
    assert len(calls)==2 and all(x.get_method()=='GET' for x in calls)


@pytest.mark.parametrize('field',['name','uuid','references','public'])
def test_content_changes_are_not_ignored(pair,field):
    c,_=pair;actual=deepcopy(c);actual[field]='changed'
    assert not compare(c,actual)['content_match']


def test_metadata_only_and_compact_output(pair,capsys):
    c,_=pair;actual={**c,'created_on':'new','content_version':2}
    diff=compare(c,actual)
    assert diff['content_match'] and not diff['exact_match'] and diff['metadata_difference_count']==2
    summary({'result':'test','post_attempted':True,'after_candidate':{'status':'present','comparison':diff}},'file.json')
    assert 'Cara II' not in capsys.readouterr().out


def receipt(pair):
    c,s=pair
    r={'format':'homebrew-as-code/myspeidel-post-verification-v1','dry_run':True,'passed':True,
       'acknowledged':True,'post_attempted':True,'result':'DRY_RUN_VERIFIED','post_http_status':200,
       'candidate_sha256':digest(c),'source_sha256':digest(s),
       'events':[{'event':'request_prepared','method':'POST','url':POST_URL,
                  'body_sha256':digest(c),'body_text':json.dumps(c)}]}
    for stage in ('before','after'):
        r[stage+'_source']={'status':'unchanged','http_status':200,'sha256':digest(s)}
        r[stage+'_candidate']={'status':'absent','http_status':404}
    return r


@pytest.mark.parametrize('failure',['hash','url','body','after','passed'])
def test_receipt_binding(pair,failure):
    r=receipt(pair);verify_receipt(r,*pair)
    if failure=='hash':r['candidate_sha256']='wrong'
    if failure=='url':r['events'][0]['url']=BASE
    if failure=='body':r['events'][0]['body_text']='{}'
    if failure=='after':r['after_candidate']['http_status']=401
    if failure=='passed':r['passed']=False
    with pytest.raises(ValueError):verify_receipt(r,*pair)


def test_existing_candidate_blocks(pair):
    c,s=pair;calls=[]
    def t(req,limit):
        calls.append(req)
        return 200,{},json.dumps(s if len(calls)==1 else c).encode()
    r=run('token',*pair,transport=t,before_send=lambda:pytest.fail('guard called'))
    assert r['result']=='PREFLIGHT_BLOCKED' and len(calls)==2


def test_get_failure_does_not_skip_other_get(pair):
    c,s=pair;calls=[]
    seq=[(200,{},json.dumps(s).encode()),(404,{},b''),
         (201,{},b'{"message":"HTTP 201 Created"}'),TimeoutError(),(200,{},json.dumps(c).encode())]
    def t(req,limit):
        calls.append(req);x=seq.pop(0)
        if isinstance(x,BaseException):raise x
        return x
    r=run('token',*pair,transport=t,before_send=lambda:None)
    assert len(calls)==5 and r['after_candidate']['status']=='present' and not r['passed']


def test_durable_guard_exclusive(tmp_path,pair):
    from homebrew_as_code.myspeidel_put_roundtrip import write_new
    marker=tmp_path/'attempt.json'
    write_new(marker,{'attempted':True})
    with pytest.raises(FileExistsError):write_new(marker,{'attempted':False})
    assert json.loads(marker.read_text())=={'attempted':True}
    with pytest.raises(ValueError):run('token',*pair)
