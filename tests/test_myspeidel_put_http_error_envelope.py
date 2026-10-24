"""0019x: opt-in local HTTP error capture and safe receipt isolation."""
import io
import json
import os
import urllib.error
from pathlib import Path

from homebrew_as_code.myspeidel_put_experiments import _write_local_http_error


def test_local_http_error_sidecar(tmp_path):
    marker = tmp_path / 'attempt.json'
    envelope = {'http_status': 400, 'content_type': 'application/json',
                'body_text': '{"message":"example"}', 'body_truncated': False,
                'body_bytes_captured': 21}
    _write_local_http_error(marker, envelope)
    value = json.loads((tmp_path / 'attempt.json.http-error.json').read_text())
    assert value['response'] == envelope
    assert 'PRIVATE' in value['warning']
    assert not marker.exists()


def test_local_http_error_is_separate_from_normal_receipt(tmp_path):
    marker = tmp_path / 'attempt.json'
    receipt = tmp_path / 'attempt.json.receipt.json'
    receipt.write_text('{"phase":"put_rejected"}')
    _write_local_http_error(marker, {'body_text': 'private error body'})
    assert 'private error body' not in receipt.read_text()
    assert 'private error body' in (tmp_path / 'attempt.json.http-error.json').read_text()
