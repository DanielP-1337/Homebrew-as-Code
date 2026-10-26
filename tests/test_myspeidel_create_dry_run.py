import json
from copy import deepcopy
from uuid import UUID
import pytest
from homebrew_as_code.myspeidel_create_dry_run import run, validate, POST_URL, NoRedirect, main
from homebrew_as_code.myspeidel_put_roundtrip import digest
from homebrew_as_code.myspeidel_create_candidate import FORMAT

TOKEN = 'test-credential-never-log'

@pytest.fixture
def pair():
    source={'uuid':str(UUID(int=1)), 'name':'Source', 'public':0, 'machine_type':{'size':20},
            'mashing':{'adds':{'malts':[]}}, 'boil':{'steps':[]},
            'fermentation':{'adds':{'yeasts':[]}}}
    candidate=deepcopy(source);candidate.update(uuid=str(UUID(int=2)),name='Candidate')
    return candidate,source


def transport_for(pair, post=(200, {}, b'{"message":"DRY RUN SUCCEEDED"}'), after_source=None, after_candidate=None):
    candidate,source=pair;calls=[]
    sequence=[(200,{},json.dumps(source).encode()),(404,{},b'{}'),post,
              after_source or (200,{},json.dumps(source).encode()),after_candidate or (404,{},b'{}')]
    def transport(req,limit):
        calls.append(req)
        result=sequence.pop(0)
        if isinstance(result,BaseException):raise result
        return result
    return transport,calls


def test_success_exact_envelope_redaction(pair):
    transport,calls=transport_for(pair)
    r=run(TOKEN,*pair,transport=transport)
    assert r['passed'] and len(calls)==5
    post=calls[2]
    assert post.get_method()=='POST' and post.full_url==POST_URL
    assert json.loads(post.data)==pair[0]
    assert TOKEN not in json.dumps(r)
    assert '[REDACTED]' in json.dumps(r)
    assert r['after_source']['status']=='unchanged' and r['after_candidate']['status']=='absent'


@pytest.mark.parametrize('post',[(400,{},b'{"error":"bad"}'),(500,{},b'oops'),
    (200,{},b'{"message":"OK"}'), (302,{'Location':'https://example.com'},b''),
    TimeoutError('secret'),KeyboardInterrupt(),(200,{},b'x'*65537)])
def test_post_failure_still_verifies_both(pair,post):
    transport,calls=transport_for(pair,post)
    r=run(TOKEN,*pair,transport=transport)
    assert len(calls)==5 and not r['passed']
    assert r['after_source']['status']=='unchanged'
    assert r['after_candidate']['status']=='absent'


@pytest.mark.parametrize('source_result,candidate_result',[
    (TimeoutError(),(404,{},b'')),((200,{},b'{}'),(200,{},b'{}')),
    ((401,{},b''),(403,{},b''))])
def test_after_failures_are_independent(pair,source_result,candidate_result):
    transport,calls=transport_for(pair,after_source=source_result,after_candidate=candidate_result)
    r=run(TOKEN,*pair,transport=transport)
    assert len(calls)==5 and not r['passed']
    assert 'after_candidate' in r


@pytest.mark.parametrize('candidate_status',[200,401,403,500])
def test_preflight_blocks_existing_or_uncertain(pair,candidate_status):
    calls=[]
    def t(req,limit):
        calls.append(req)
        return (200,{},json.dumps(pair[1]).encode()) if len(calls)==1 else (candidate_status,{},b'{}')
    r=run(TOKEN,*pair,transport=t)
    assert not r['post_attempted'] and len(calls)==2


def test_changed_source_blocks(pair):
    def t(req,limit): return 200,{},json.dumps({**pair[1],'name':'changed'}).encode()
    assert not run(TOKEN,*pair,transport=t)['post_attempted']


def test_integrity_and_source_identity(pair):
    c,s=pair
    spec={'paths':{'/v1.0/recipe':{'post':{'parameters':[{'name':'dryRun','in':'query'}],
        'requestBody':{'content':{'application/json':{'schema':{'type':'object'}}}}}}}}
    a={'format':FORMAT,'candidate':c,'report':{'candidate_sha256':digest(c),'source_sha256':digest(s)}}
    assert validate(a,s,spec)[0]==c
    c['uuid']=s['uuid'];a['report']['candidate_sha256']=digest(c)
    with pytest.raises(ValueError):validate(a,s,spec)
    c['name']='tamper'
    with pytest.raises(ValueError):validate(a,s,spec)


def test_no_redirect():
    assert NoRedirect().redirect_request(None,None,None,None,None,None) is None


def test_cli_missing_files_no_network(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(['--candidate','.local/missing','--backup','.local/backup',
                 '--spec','spec.json','--diagnostics','.local/result'])==2
    assert not (tmp_path/'.local/result').exists()


def test_error_response_credentials_masked(pair):
    body=json.dumps({'password':'hidden-password','detail':'Bearer '+TOKEN,'token':TOKEN}).encode()
    t,_=transport_for(pair,(400,{'Set-Cookie':'session=hidden-cookie'},body))
    text=json.dumps(run(TOKEN,*pair,transport=t))
    assert all(secret not in text for secret in (TOKEN,'hidden-password','hidden-cookie'))


def test_source_changed_after_post(pair):
    changed={**pair[1],'name':'changed'}
    t,calls=transport_for(pair,after_source=(200,{},json.dumps(changed).encode()))
    r=run(TOKEN,*pair,transport=t)
    assert r['after_source']['status']=='changed' and not r['passed'] and len(calls)==5


def test_real_transport_redirect_and_bounded_read(monkeypatch):
    from homebrew_as_code.myspeidel_create_dry_run import exchange
    import urllib.request
    seen={}
    class Response:
        code=200
        headers={}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):seen['read']=n;return b'{}'
    class Opener:
        def open(self,request,timeout):seen['timeout']=timeout;return Response()
    def build(handler):
        assert isinstance(handler,NoRedirect)
        return Opener()
    monkeypatch.setattr(urllib.request,'build_opener',build)
    assert exchange(urllib.request.Request(POST_URL),64)[0]==200
    assert seen=={'read':65,'timeout':20}
