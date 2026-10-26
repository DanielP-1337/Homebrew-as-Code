"""No network: capture actual Request bytes and independently test failure GET paths."""
import io
import json
import urllib.error
from email.message import Message

import pytest

from homebrew_as_code.myspeidel_put_roundtrip import (
    PutDiagnosticError, digest, put_recipe, write_new,
)
from homebrew_as_code.myspeidel_dev_diagnostics import body_view
from homebrew_as_code import myspeidel_put_roundtrip_cli as cli

UUID = '123e4567-e89b-12d3-a456-426614174000'
TOKEN = 'test-bearer-credential-unique'


def sample():
    return {'uuid': UUID, 'public': 0, 'machine_type': {'size': 20},
            'name': 'Development recipe', 'schema_version': 2}


def test_http_400_captures_request_response_and_masks_credentials():
    events = []
    rec = sample()
    rec['password'] = 'synthetic-password'
    sent = []
    def opener(req, timeout):
        sent.append(req)
        headers = Message()
        headers['Content-Type'] = 'application/json'
        headers['Set-Cookie'] = 'session=secret-cookie'
        body = json.dumps({'errors': [{'path': '$.references.water_types.demo.name',
                                      'message': 'Expected string, got null'}],
                           'access_token': 'another-secret', 'echo': TOKEN,
                           'nested': {'password': 'response-password'}}).encode()
        raise urllib.error.HTTPError(req.full_url, 400, 'Bad Request', headers, io.BytesIO(body))
    with pytest.raises(PutDiagnosticError):
        put_recipe(TOKEN, UUID, rec, dry_run=True, opener=opener, diagnostic_events=events)
    request, response = events
    assert sent[0].data == json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    assert request['body_sha256'] == digest(rec)
    assert request['body_bytes'] == len(sent[0].data)
    assert request['url'].endswith('?dryRun=1')
    assert not request['backup_wrapper_detected']
    assert response['http_status'] == 400
    assert response['body']['errors'][0]['message'] == 'Expected string, got null'
    output = json.dumps(events)
    for secret in (TOKEN, 'synthetic-password', 'secret-cookie', 'another-secret', 'response-password'):
        assert secret not in output
    assert 'Development recipe' in output and UUID in output


def test_unredacted_request_text_equals_actual_payload():
    events = []
    class Response:
        status = 200
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit): return b'{"message":"DRY RUN SUCCEEDED"}'
    def opener(req, timeout):
        assert events[0]['body_text'].encode() == req.data
        return Response()
    assert put_recipe(TOKEN, UUID, sample(), dry_run=True, opener=opener, diagnostic_events=events) == 200
    assert events[1]['body']['message'] == 'DRY RUN SUCCEEDED'


def test_text_response_redaction_and_truncation():
    from homebrew_as_code.myspeidel_dev_diagnostics import response_event
    text = 'Authorization: Bearer secret\npassword="hidden value"\naccess_token=hidden2\n' + TOKEN
    result = body_view(text.encode(), TOKEN)
    assert all(v not in result['body_text'] for v in ('secret', 'hidden value', 'hidden2', TOKEN))
    result = response_event(502, {}, b'x' * 11, TOKEN, 10)
    assert result['body_truncated'] and result['body_bytes_captured'] == 10


def test_no_verbose_real_write():
    with pytest.raises(ValueError, match='dry_run=True'):
        put_recipe(TOKEN, UUID, sample(), dry_run=False, diagnostic_events=[])


@pytest.mark.parametrize('put_outcome', ['ok', 'http400', 'timeout', 'bad_ack'])
@pytest.mark.parametrize('get_outcome', ['unchanged', 'changed', 'unverified'])
def test_cli_always_checks_get_and_gates_receipt(tmp_path, monkeypatch, capsys, put_outcome, get_outcome):
    monkeypatch.chdir(tmp_path)
    rec = sample()
    from pathlib import Path
    backup = Path('.local/backup.json')
    write_new(backup, {'format': 'homebrew-as-code/myspeidel-put-backup-v1',
                      'uuid': UUID, 'recipe': rec, 'sha256': digest(rec)})
    calls = []
    class Client:
        def get_recipe(self, uuid):
            calls.append('GET')
            if len(calls) == 1 or get_outcome == 'unchanged': return rec.copy()
            if get_outcome == 'changed': return {**rec, 'name': 'changed'}
            raise cli.MySpeidelError('unavailable')
    monkeypatch.setattr(cli, '_login', lambda: (TOKEN, Client()))
    monkeypatch.setattr('builtins.input', lambda _: 'yes')
    def put(token, uuid, recipe, *, dry_run, diagnostic_events):
        calls.append('PUT')
        assert dry_run is True and recipe == rec
        diagnostic_events.append({'event': 'synthetic', 'echo': TOKEN})
        if put_outcome != 'ok':
            raise PutDiagnosticError(400 if put_outcome == 'http400' else None, put_outcome)
    monkeypatch.setattr(cli, 'put_recipe', put)
    status = cli.main(['dry-run', '--backup', str(backup), '--receipt', '.local/receipt.json',
                       '--diagnostics', '.local/diagnostics.json'])
    assert calls == ['GET', 'PUT', 'GET']
    success = put_outcome == 'ok' and get_outcome == 'unchanged'
    assert status == (0 if success else 1)
    assert Path('.local/receipt.json').exists() is success
    report = json.loads(Path('.local/diagnostics.json').read_text())
    assert report['verification']['status'] == get_outcome
    assert report['put_result'] == ('acknowledged' if put_outcome == 'ok' else 'failed')
    captured = capsys.readouterr()
    assert TOKEN not in captured.out + captured.err + json.dumps(report)
