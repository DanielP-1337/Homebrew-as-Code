"""One explicitly confirmed live POST, durable attempt guard and GET comparison."""
import argparse
import json
from pathlib import Path
import urllib.request
from uuid import UUID

from .myspeidel_create_dry_run import (BASE, POST_URL, LIMIT, RESPONSE_LIMIT, NoRedirect,
                                      exchange, read_json, validate)
from .myspeidel_put_roundtrip import digest, serialized, private_file, read_backup, write_new, check_private
from .myspeidel_dev_diagnostics import redact, request_event, response_event

METADATA = {'created_on', 'creation_date', 'update_on', 'content_version'}


def verify_receipt(receipt, candidate, source):
    if (receipt.get('format') != 'homebrew-as-code/myspeidel-post-verification-v1'
            or receipt.get('dry_run') is not True or receipt.get('passed') is not True
            or receipt.get('acknowledged') is not True or receipt.get('post_attempted') is not True
            or receipt.get('result') != 'DRY_RUN_VERIFIED' or receipt.get('post_http_status') != 200
            or receipt.get('candidate_sha256') != digest(candidate)
            or receipt.get('source_sha256') != digest(source)):
        raise ValueError('No matching successful 0020s dry-run evidence')
    for stage in ('before', 'after'):
        src, new = receipt.get(stage+'_source', {}), receipt.get(stage+'_candidate', {})
        if (src.get('status') != 'unchanged' or src.get('sha256') != digest(source)
                or src.get('http_status') != 200 or new.get('status') != 'absent'
                or new.get('http_status') != 404):
            raise ValueError('Dry-run GET evidence incomplete')
    requests = [e for e in receipt.get('events', []) if e.get('event') == 'request_prepared']
    if len(requests) != 1:
        raise ValueError('Expected exactly one dry-run request')
    req = requests[0]
    if (req.get('method') != 'POST' or req.get('url') != POST_URL
            or req.get('body_sha256') != digest(candidate)
            or json.loads(req['body_text']) != candidate):
        raise ValueError('Dry-run request does not match candidate')


def compare(expected, actual):
    """Exact comparison; only timestamp/content-version differences are classified metadata."""
    changes = []
    def walk(a, b, path, metadata=False):
        if type(a) is not type(b) and not (type(a) in (int,float) and type(b) in (int,float)):
            changes.append({'path':path,'expected':a,'actual':b,'metadata':metadata}); return
        if isinstance(a, dict):
            for key in sorted(set(a)|set(b)):
                meta = metadata or key in METADATA
                if key not in a or key not in b:
                    changes.append({'path':path+'/'+key,'expected_present':key in a,
                                    'actual_present':key in b,'expected':a.get(key),'actual':b.get(key),'metadata':meta})
                else: walk(a[key],b[key],path+'/'+key,meta)
        elif isinstance(a,list):
            if len(a)!=len(b):
                changes.append({'path':path,'expected':a,'actual':b,'metadata':metadata})
            else:
                for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i),metadata)
        elif a!=b: changes.append({'path':path,'expected':a,'actual':b,'metadata':metadata})
    walk(expected,actual,'')
    return {'exact_match':not changes, 'content_match':not any(not x['metadata'] for x in changes),
            'differences':changes, 'metadata_difference_count':sum(x['metadata'] for x in changes),
            'content_difference_count':sum(not x['metadata'] for x in changes)}


def run(token, candidate, source, *, transport=exchange, before_send=None, verify_only=False):
    if not token or '\r' in token or '\n' in token:
        raise ValueError('Invalid token')
    if not verify_only and before_send is None:
        raise ValueError('Durable attempt guard required')
    headers={'Authorization':'Bearer '+token,'Accept':'application/json','User-Agent':'Homebrew-as-Code/0020t'}
    report={'format':'homebrew-as-code/myspeidel-live-create-v1', 'candidate_sha256':digest(candidate),
            'source_sha256':digest(source),'candidate_uuid':candidate['uuid'], 'events':[],
            'post_attempted':False,'verify_only':verify_only,'passed':False}
    def get(uid, baseline=None):
        try:
            req=urllib.request.Request(BASE+'/'+str(UUID(uid)),headers=headers,method='GET')
            status,hs,body=transport(req,LIMIT)
            event=response_event(status,hs,body,token,RESPONSE_LIMIT)
            event.update(method='GET',url=req.full_url);report['events'].append(event)
            if status==404:return {'status':'absent','http_status':404}
            if status!=200 or len(body)>LIMIT:return {'status':'unverified','http_status':status}
            obj=check_private(json.loads(body),uid)
            result={'status':'present','http_status':status,'sha256':digest(obj)}
            if baseline is not None:
                result['status']='unchanged' if result['sha256']==baseline else 'changed'
            else:
                result['recipe']=obj
                result['comparison']=compare(candidate,obj)
            return result
        except (Exception,KeyboardInterrupt) as exc:
            return {'status':'unverified','error_type':type(exc).__name__}
    if not verify_only:
        report['before_source']=get(source['uuid'],digest(source))
        report['before_candidate']=get(candidate['uuid'])
        if (report['before_source']['status']!='unchanged' or report['before_candidate']['status']!='absent'):
            report['result']='PREFLIGHT_BLOCKED';return redact(report,token)
        try:
            req=urllib.request.Request(BASE,data=serialized(candidate),method='POST',
                                       headers={**headers,'Content-Type':'application/json'})
            report['events'].append(request_event(req,token))
            before_send()  # Exclusive durable marker MUST succeed before request.
            report['post_attempted']=True
            status,hs,body=transport(req,RESPONSE_LIMIT)
            report['events'].append(response_event(status,hs,body,token,RESPONSE_LIMIT))
            report['post_http_status']=status
            report['created_acknowledged']=(status==201 and len(body)<=RESPONSE_LIMIT
                and json.loads(body).get('message')=='HTTP 201 Created')
        except (Exception,KeyboardInterrupt) as exc:
            report['post_error_type']=type(exc).__name__
        finally:
            report['after_source']=get(source['uuid'],digest(source))
            report['after_candidate']=get(candidate['uuid'])
    else:
        report['after_source']=get(source['uuid'],digest(source))
        report['after_candidate']=get(candidate['uuid'])
    new=report['after_candidate']
    verified=(report['after_source']['status']=='unchanged' and new['status']=='present'
              and new.get('comparison',{}).get('content_match') is True)
    report['passed']=verified and (verify_only or report.get('created_acknowledged') is True)
    report['result']=('GET_COMPARISON_VERIFIED' if verify_only else 'LIVE_CREATE_VERIFIED') if report['passed'] else 'FAILED_OR_UNVERIFIED'
    return redact(report,token)


def summary(report, path):
    print('Result:',report['result'])
    print('POST attempted:',report['post_attempted'],'HTTP:',report.get('post_http_status','n/a'))
    for label in ('before_source','before_candidate','after_source','after_candidate'):
        if label in report:print(label+':',report[label]['status'])
    comp=report.get('after_candidate',{}).get('comparison')
    if comp:
        print('Content differences:',comp['content_difference_count'],
              'metadata differences:',comp['metadata_difference_count'])
    print('Diagnostics:',path)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','backup','receipt','spec','diagnostics'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--verify-only',action='store_true',help='GET only; never send recipe POST')
    parser.add_argument('--verbose',action='store_true',help='Print full masked diagnostics')
    args=parser.parse_args(argv)
    try:
        destination=private_file(args.diagnostics)
        artifact=read_json(private_file(args.candidate,must_exist=True))
        _,source,_=read_backup(private_file(args.backup,must_exist=True))
        candidate,contract=validate(artifact,source,read_json(Path(args.spec)))
        receipt=read_json(private_file(args.receipt,must_exist=True))
        verify_receipt(receipt,candidate,source)
        marker=Path('.local/myspeidel-create-attempts')/(candidate['uuid']+'.json')
        if marker.exists() and not args.verify_only:
            raise ValueError('Attempt marker exists. Use --verify-only; do not repeat POST.')
        print('Source:',json.dumps(source['name'],ensure_ascii=True))
        print('New recipe:',json.dumps(candidate['name'],ensure_ascii=True),candidate['uuid'])
        print('Candidate SHA256:',digest(candidate))
        if not args.verify_only:
            print('REAL CREATE: the candidate will be saved as a new private recipe.')
            if input('Type CREATE PRIVATE RECIPE to proceed: ').strip()!='CREATE PRIVATE RECIPE':
                print('Cancelled; no HTTP.');return 0
        write_new(destination,{'status':'STARTED_RESULTS_UNKNOWN','candidate_sha256':digest(candidate)})
        from .myspeidel_auth import login
        from .myspeidel_credentials import prompt_credentials
        username,password=prompt_credentials()
        token=login(username,password,opener=urllib.request.build_opener(NoRedirect()).open)
        def reserve():
            write_new(marker,{'status':'ATTEMPTED_CHECK_SERVER_BEFORE_RETRY',
                              'candidate_uuid':candidate['uuid'],'candidate_sha256':digest(candidate),
                              'diagnostics':str(destination)})
        result=run(token,candidate,source,before_send=reserve,verify_only=args.verify_only)
        result['offline_contract']=contract
        result['dry_run_receipt_sha256']=digest(receipt)
        result=redact(result,token)
        destination.write_text(json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf-8')
        summary(result,destination)
        if args.verbose:print(json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False))
        return 0 if result['passed'] else 2
    except (Exception,KeyboardInterrupt) as exc:
        # Exception text from auth/transport can contain credentials.
        print('Stopped:',type(exc).__name__, '; check paths, evidence and attempt marker. Use --verify-only after an attempt.')
        return 2


if __name__=='__main__':
    raise SystemExit(main())
