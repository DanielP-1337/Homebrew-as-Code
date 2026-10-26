"""0020s: bounded POST dryRun=1 and independent before/after GET evidence."""
import argparse
import json
import urllib.request
import urllib.error
from uuid import UUID

from .myspeidel_create_candidate import FORMAT, additions
from .myspeidel_import_builder import inspect_create_contract
from .myspeidel_put_roundtrip import digest, serialized as canonical, private_file, read_backup, write_new, check_private
from .myspeidel_post_dry_run import dry_run_acknowledged
from .myspeidel_dev_diagnostics import redact, request_event, response_event

BASE = 'https://api.cloud.myspeidel.com/v1.0/recipe'
POST_URL = BASE + '?dryRun=1'
LIMIT = 5_000_000
RESPONSE_LIMIT = 65_536


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def exchange(request, limit):
    """No retries, no redirects, bounded response and timeout."""
    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=20)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.code, response.headers, response.read(limit + 1)


def validate(artifact, source, spec):
    if artifact.get('format') != FORMAT:
        raise ValueError('Expected 0020r candidate artifact')
    candidate, report = artifact['candidate'], artifact['report']
    if digest(candidate) != report['candidate_sha256'] or digest(source) != report['source_sha256']:
        raise ValueError('Candidate or source digest mismatch')
    check_private(candidate, candidate['uuid'])
    ids = [candidate['uuid']] + [x['uuid'] for x in additions(candidate)]
    for value in ids:
        if str(UUID(value)) != value:
            raise ValueError('Noncanonical UUID')
    old_ids = {source['uuid']} | {x['uuid'] for x in additions(source)}
    if len(ids) != len(set(ids)) or old_ids.intersection(ids):
        raise ValueError('Recipe/addition UUIDs must be new and unique')
    if len(canonical(candidate)) > LIMIT:
        raise ValueError('Candidate too large')
    contract = inspect_create_contract(spec, candidate)
    if contract['schema_errors'] or not contract['dry_run_documented']:
        raise ValueError('POST contract errors or missing dryRun parameter')
    return candidate, contract


def run(token, candidate, source, *, transport=exchange):
    if not token or '\r' in token or '\n' in token:
        raise ValueError('Invalid token')
    report = {'format': 'homebrew-as-code/myspeidel-post-verification-v1',
              'dry_run': True, 'candidate_sha256': digest(candidate),
              'source_sha256': digest(source), 'events': [], 'post_attempted': False,
              'acknowledged': False, 'passed': False}
    headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json',
               'User-Agent': 'Homebrew-as-Code/0020s'}

    def probe(uuid, baseline=None):
        try:
            req = urllib.request.Request(BASE + '/' + str(UUID(uuid)), headers=headers, method='GET')
            status, response_headers, body = transport(req, LIMIT)
            event = response_event(status, response_headers, body, token, RESPONSE_LIMIT)
            event.update(method='GET', url=req.full_url)
            report['events'].append(event)
            if baseline is None:
                return {'status': 'absent' if status == 404 else 'present' if status == 200 else 'unverified',
                        'http_status': status}
            if status != 200 or len(body) > LIMIT:
                return {'status': 'unverified', 'http_status': status}
            current = check_private(json.loads(body), uuid)
            after = digest(current)
            return {'status': 'unchanged' if after == baseline else 'changed',
                    'http_status': status, 'sha256': after}
        except (OSError, ValueError, KeyError, TypeError, KeyboardInterrupt) as exc:
            return {'status': 'unverified', 'error_type': type(exc).__name__}

    report['before_source'] = probe(source['uuid'], digest(source))
    report['before_candidate'] = probe(candidate['uuid'])
    if report['before_source']['status'] != 'unchanged' or report['before_candidate']['status'] != 'absent':
        report['result'] = 'PREFLIGHT_BLOCKED'
        return redact(report, token)
    try:
        req = urllib.request.Request(POST_URL, data=canonical(candidate), method='POST',
                                     headers={**headers, 'Content-Type': 'application/json'})
        report['events'].append(request_event(req, token))
        report['post_attempted'] = True
        status, response_headers, body = transport(req, RESPONSE_LIMIT)
        report['events'].append(response_event(status, response_headers, body, token, RESPONSE_LIMIT))
        report['acknowledged'] = (status == 200 and len(body) <= RESPONSE_LIMIT
                                  and dry_run_acknowledged(body))
        report['post_http_status'] = status
    except (OSError, ValueError, KeyError, TypeError, KeyboardInterrupt) as exc:
        report['post_error_type'] = type(exc).__name__
    finally:
        # Independent probes: a failed source GET must not skip candidate GET.
        report['after_source'] = probe(source['uuid'], digest(source))
        report['after_candidate'] = probe(candidate['uuid'])
    report['passed'] = (report['acknowledged'] and report['after_source']['status'] == 'unchanged'
                        and report['after_candidate']['status'] == 'absent')
    report['result'] = 'DRY_RUN_VERIFIED' if report['passed'] else 'FAILED_OR_UNVERIFIED'
    return redact(report, token)


def read_json(path):
    if path.stat().st_size > LIMIT:
        raise ValueError('Input exceeds size limit')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'backup', 'spec', 'diagnostics'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        destination = private_file(args.diagnostics)
        if destination.exists():
            raise ValueError('Diagnostics path already exists')
        artifact = read_json(private_file(args.candidate, must_exist=True))
        _, source, _ = read_backup(private_file(args.backup, must_exist=True))
        from pathlib import Path
        candidate, contract = validate(artifact, source, read_json(Path(args.spec)))
        print('Source recipe:', json.dumps(source['name'], ensure_ascii=True))
        print('Candidate:', json.dumps(candidate['name'], ensure_ascii=True), candidate['uuid'])
        print('Candidate SHA256:', digest(candidate))
        print('Unverified schema constraints:', len(contract['unverified_constraints']))
        if input('Perform POST dryRun=1 and GET verification? [yes/NO]: ').strip() != 'yes':
            print('Cancelled; no HTTP.'); return 0
        # Reserve before login/network. A hard interruption leaves an explicit marker.
        write_new(destination, {'status': 'STARTED_RESULTS_UNKNOWN', 'candidate_sha256': digest(candidate)})
        from .myspeidel_credentials import prompt_credentials
        from .myspeidel_auth import login
        username, password = prompt_credentials()
        token = login(username, password, opener=urllib.request.build_opener(NoRedirect()).open)
        result = run(token, candidate, source)
        result['offline_contract'] = contract
        result = redact(result, token)
        destination.write_text(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        print('Result:', result['result'])
        return 0 if result['passed'] else 2
    except (Exception, KeyboardInterrupt) as exc:
        # Authentication/network exceptions may embed credentials; print only type.
        print('Stopped:', type(exc).__name__, '; inspect diagnostics marker if present. No automatic retry.')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
