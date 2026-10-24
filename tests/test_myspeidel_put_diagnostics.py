import io
import urllib.error

import pytest

from homebrew_as_code.myspeidel_put_roundtrip import (
    PutDiagnosticError, classify_put_error, dry_run_acknowledged, put_recipe,
)

UUID = '123e4567-e89b-12d3-a456-426614174000'
RECIPE = {'uuid': UUID, 'public': 0, 'machine_type': {'size': 20}}


def response(data, status=200):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, size): return data
    r = Response()
    r.status = status
    return r


def test_dry_run_ack_required():
    for body in (b'{}', b'', b'{"message":"no"}', b'[]'):
        with pytest.raises(PutDiagnosticError) as e:
            put_recipe('secret', UUID, RECIPE, dry_run=True, opener=lambda *_, **kw: response(body))
        assert e.value.category == 'dry_run_ack_unverified'
        assert e.value.status == 200
    assert dry_run_acknowledged(b'{"message": "DRY RUN SUCCEEDED"}')


def test_http_error_redacts_private_response():
    body = b'{"message":"private SECRET RECIPE", "errors":[{"path":"$.mashing.adds.malts[0].uuid", "message":"SECRET"}]}'
    def opener(*_, **kw):
        raise urllib.error.HTTPError('https://redacted', 400, 'Bad Request', {}, io.BytesIO(body))
    with pytest.raises(PutDiagnosticError) as e:
        put_recipe('secret', UUID, RECIPE, dry_run=True, opener=opener)
    assert e.value.status == 400
    assert e.value.category == 'schema_validation'
    assert e.value.location == 'mashing'
    assert 'SECRET' not in str(e.value)


def test_unknown_and_non_json_responses_are_not_echoed():
    assert classify_put_error(b'<html>secret</html>') == ('unclassified', 'unknown')
    assert classify_put_error(b'{"error":"secret uuid"}') == ('server_rejection', 'unknown')
    assert classify_put_error(b'{"errors":[{"path":"$.secret-token"}]}') == ('schema_validation', 'unknown')
