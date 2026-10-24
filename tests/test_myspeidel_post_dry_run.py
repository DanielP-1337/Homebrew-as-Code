import io
import json
import urllib.error
import uuid

import pytest

from homebrew_as_code.myspeidel_post_dry_run import (
    DRY_RUN_URL, inspect, prepare, send_dry_run, sha256,
)


@pytest.fixture
def source():
    return {'uuid': str(uuid.uuid4()), 'name': 'Original', 'public': 0,
            'machine_type': {'size': 20},
            'references': {'malts': {'x': {'name': 'Malt'}}, 'hops': {}},
            'mashing': {'adds': {'malts': []}}}


def test_prepare_does_not_mutate_source(source):
    prev = json.dumps(source, sort_keys=True)
    new = prepare(source, title='HBAC Dry Run', new_uuid=str(uuid.uuid4()))
    assert json.dumps(source, sort_keys=True) == prev
    assert new['uuid'] != source['uuid'] and new['public'] == 0
    assert inspect(new)['status'] == 'OFFLINE_PREPARED'


def test_reject_same_title_and_uuid(source):
    with pytest.raises(ValueError):
        prepare(source, title='Original', new_uuid=str(uuid.uuid4()))
    with pytest.raises(ValueError):
        prepare(source, title='New', new_uuid=source['uuid'])


def test_disallows_public_or_different_machine(source):
    source['public'] = 1
    with pytest.raises(ValueError):
        inspect(source)
    source['public'] = 0
    source['machine_type']['size'] = 50
    with pytest.raises(ValueError):
        inspect(source)


def test_no_live_post_possible(source):
    reqs = []
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, n): return b'DRY RUN SUCCEEDED'
    def opener(req, timeout):
        reqs.append(req)
        return Response()
    result = send_dry_run('test-token', source, opener=opener)
    assert result['acknowledged'] is True
    assert len(reqs) == 1
    assert reqs[0].full_url == DRY_RUN_URL
    assert reqs[0].get_method() == 'POST'
    assert b'test-token' not in reqs[0].data


def test_200_without_ack_not_success(source):
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, n): return b'{"message":"created"}'
    assert not send_dry_run('token', source, opener=lambda req, timeout: Response())['acknowledged']


def test_400_error_sanitized(source):
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 400, 'Bad', {}, io.BytesIO(
            b'{"errors":[{"path":"$.references.malts.secret-ID","message":"private ingredient"}]}'))
    result = send_dry_run('token', source, opener=opener)
    assert result['http_status'] == 400
    assert 'private ingredient' not in json.dumps(result)
    assert not result['acknowledged']


def test_sha_stability(source):
    assert sha256(source) == sha256(json.loads(json.dumps(source)))
