"""Safe diagnostics contain no user-controlled strings or identifying keys."""
import json
from homebrew_as_code.myspeidel_server_validation import summarize_server_validation


def test_mask_uuid_and_reject_private_message():
    response = {"message": "SECRET PASSWORD", "errors": [
        {"path": "$.references.hops.SECRET_HOP_UUID.name", "message": "SECRET PASSWORD", "errorCode": "openapivalidation"},
        {"path": "$.owner.name", "errorCode": "type"},
    ]}
    result = summarize_server_validation(json.dumps(response).encode())
    assert result['error_count'] == 2
    assert result['safe_paths'] == ['$.owner.name', '$.references.hops.<redacted>.name']
    assert result['known_error_codes'] == ['openapivalidation', 'type']
    assert 'SECRET' not in json.dumps(result)


def test_ignore_unknown_error_code_and_path():
    obj = {"errors": [{"path": "$.SECRET_ROOT.foo", "errorCode": "PRIVATE_CODE"},
                      {"path": "$.references.hops[44].name", "errorCode": "required"}]}
    result = summarize_server_validation(json.dumps(obj).encode())
    assert result['safe_paths'] == ['$.references.hops[*].name']
    assert result['pathless_errors'] == 1
    assert result['known_error_codes'] == ['required']


def test_invalid_truncated_and_non_json():
    assert summarize_server_validation(b'<html>private</html>')['response_format'] == 'unknown'
    assert summarize_server_validation(b'X' * 65537)['response_format'] == 'oversized_or_unavailable'
    assert summarize_server_validation(b'{"message":"secret"}')['response_format'] == 'json_without_errors_array'
    report = summarize_server_validation(json.dumps({'errors': [{}] * 40}).encode())
    assert report['error_count'] == 32
    assert report['error_count_truncated'] is True


def test_validation_summary_attached_to_receipt(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import pytest
    from homebrew_as_code import myspeidel_put_experiments as exp
    from homebrew_as_code.myspeidel_put_roundtrip import PutDiagnosticError
    from homebrew_as_code import myspeidel_put_roundtrip_cli as cli

    baseline = {'public': 0, 'name': 'fake'}
    sha = exp.digest(baseline)
    marker = tmp_path / 'attempt.json'
    monkeypatch.setattr(exp, 'private_file', lambda value: marker)
    monkeypatch.setattr(exp, '_current', lambda client, uuid: baseline)
    monkeypatch.setattr(cli, '_login', lambda: ('fake', object()))
    monkeypatch.setattr('builtins.input', lambda prompt: 'DRY RUN EXPERIMENT')

    def reject(*args, **kwargs):
        failure = PutDiagnosticError(400, 'schema_validation', 'unknown')
        failure.validation_details = summarize_server_validation(json.dumps({
            'errors': [{'path': '$.references.hops.SECRET_KEY.name',
                        'message': 'SECRET_MESSAGE', 'errorCode': 'openapivalidation'}]
        }).encode())
        raise failure

    monkeypatch.setattr(exp, 'put_recipe', reject)
    args = SimpleNamespace(result=str(marker), variant='omit-null-names', mode='dry-run')
    with pytest.raises(PutDiagnosticError):
        exp._run_online(args, 'private-uuid', baseline, sha, baseline, 'different-candidate')
    receipt = json.loads((tmp_path / 'attempt.json.receipt.json').read_text())
    assert receipt['validation_details']['safe_paths'] == ['$.references.hops.<redacted>.name']
    assert receipt['server_state'] == 'baseline_match'
    assert 'SECRET' not in json.dumps(receipt)


def test_error_shape_inspector_never_leaks_dynamic_keys_or_values():
    source = {'errors': [
        {'path': ['SECRET_UUID'], 'message': 'SECRET_PASSWORD',
         'errorCode': 'SECRET_CODE', 'private_secret': 'SECRET_TOKEN'},
        {'path': ['OTHER_ID'], 'message': 'ANOTHER_SECRET',
         'errorCode': 'OTHER_CODE', 'different_secret': 'SECRET'},
        {'path': {'sensitive': 'SECRET'}, 'params': {'private': 'SECRET'}},
    ]}
    report = summarize_server_validation(json.dumps(source).encode())
    assert report['error_count'] == 3
    assert report['pathless_errors'] == 3
    assert report['error_shapes'] == [
        {'count': 1, 'kind': 'object',
         'fields': {'params': 'object', 'path': 'object'}, 'other_key_count': 0},
        {'count': 2, 'kind': 'object',
         'fields': {'errorCode': 'string', 'message': 'string', 'path': 'array'},
         'other_key_count': 1},
    ] or sorted(s['count'] for s in report['error_shapes']) == [1, 2]
    assert 'SECRET' not in json.dumps(report)
    assert 'private_secret' not in json.dumps(report)


def test_error_shape_inspector_is_bounded_and_safe_with_unusual_values():
    source = {'errors': [{'message': None, 'code': False, 'details': [1],
                          'field': 2.5, 'location': {'token': 'SECRET'}}] * 40}
    report = summarize_server_validation(json.dumps(source).encode())
    assert report['error_count'] == 32
    assert report['error_count_truncated'] is True
    assert report['error_shapes'][0]['count'] == 32
    assert report['error_shapes'][0]['fields'] == {
        'code': 'boolean', 'details': 'array', 'field': 'number',
        'location': 'object', 'message': 'null',
    }
    assert 'SECRET' not in json.dumps(report)


def test_path_formats_and_masking_without_plaintext(monkeypatch):
    monkeypatch.delenv('HBAC_MYSPEIDEL_LOCAL_PLAINTEXT_PATHS', raising=False)
    response = {'errors': [
        {'path': '/references/hops/SECRET_KEY/name'},
        {'path': 'references.water_types.SECRET_ID.name'},
        {'path': '$.references.hops.SECRET_ID.name'},
        {'path': 'mashing.steps[0].temperature'},
        {'path': ''},
    ]}
    report = summarize_server_validation(json.dumps(response).encode())
    assert report['path_formats'] == {'dot': 1, 'empty': 1, 'json_pointer': 1, 'jsonpath': 1, 'bracket': 1}
    assert '$.references.hops.<redacted>.name' in report['masked_path_patterns']
    assert 'local_plaintext_paths' not in report
    assert 'SECRET' not in json.dumps(report)


def test_plaintext_paths_require_explicit_opt_in(monkeypatch):
    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_PLAINTEXT_PATHS', '1')
    body = {'errors': [{'path': '/references/hops/SECRET_KEY/name',
                        'message': 'SECRET_MESSAGE', 'errorCode': 'SECRET_CODE'}]}
    report = summarize_server_validation(json.dumps(body).encode())
    assert report['local_plaintext_paths'] == ['/references/hops/SECRET_KEY/name']
    assert 'SECRET_MESSAGE' not in json.dumps(report)
    assert 'SECRET_CODE' not in json.dumps(report)
    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_PLAINTEXT_PATHS', 'true')
    assert 'local_plaintext_paths' not in summarize_server_validation(json.dumps(body).encode())


def test_non_string_and_long_paths_are_not_copied_even_if_enabled(monkeypatch):
    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_PLAINTEXT_PATHS', '1')
    report = summarize_server_validation(json.dumps({'errors': [
        {'path': {'secret': 'VALUE'}}, {'path': 'S' * 513}, {'path': None}
    ]}).encode())
    assert report['local_plaintext_paths'] == []
    assert 'VALUE' not in json.dumps(report)
    assert 'SSSSSS' not in json.dumps(report)


def test_local_full_errors_preserve_order_and_duplicate_paths(monkeypatch):
    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS', '1')
    body = {'message': 'TOP_LEVEL_SECRET', 'errors': [
        {'path': '/body/name', 'errorCode': 'abc', 'message': 'First', 'token': 'DO_NOT_COPY'},
        {'path': '/body/name', 'errorCode': 'xyz', 'message': 'Second'},
    ]}
    result = summarize_server_validation(json.dumps(body).encode())
    assert result['local_full_errors'] == [
        {'path': '/body/name', 'errorCode': 'abc', 'message': 'First'},
        {'path': '/body/name', 'errorCode': 'xyz', 'message': 'Second'},
    ]
    assert 'TOP_LEVEL_SECRET' not in json.dumps(result)
    assert 'DO_NOT_COPY' not in json.dumps(result)


def test_local_full_errors_disabled_and_bounded(monkeypatch):
    monkeypatch.delenv('HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS', raising=False)
    response = json.dumps({'errors': [{'message': 'SECRET'}]}).encode()
    assert 'local_full_errors' not in summarize_server_validation(response)
    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS', '1')
    report = summarize_server_validation(json.dumps({'errors': [
        {'path': '/body', 'message': 'X' * 2049, 'errorCode': 42}
    ]}).encode())
    assert report['local_full_errors'] == [
        {'path': '/body', 'message': None, 'errorCode': None}
    ]


def test_local_full_errors_sidecar_separate_from_receipt(tmp_path, monkeypatch):
    from types import SimpleNamespace
    import pytest
    from homebrew_as_code import myspeidel_put_experiments as exp
    from homebrew_as_code.myspeidel_put_roundtrip import PutDiagnosticError
    from homebrew_as_code import myspeidel_put_roundtrip_cli as cli

    monkeypatch.setenv('HBAC_MYSPEIDEL_LOCAL_FULL_ERRORS', '1')
    monkeypatch.delenv('HBAC_MYSPEIDEL_LOCAL_PLAINTEXT_PATHS', raising=False)
    baseline = {'public': 0, 'name': 'test'}
    sha = exp.digest(baseline)
    marker = tmp_path / 'attempt.json'
    monkeypatch.setattr(exp, 'private_file', lambda value: marker)
    monkeypatch.setattr(exp, '_current', lambda client, uuid: baseline)
    monkeypatch.setattr(cli, '_login', lambda: ('fake', object()))
    monkeypatch.setattr('builtins.input', lambda prompt: 'DRY RUN EXPERIMENT')

    def reject(*args, **kwargs):
        exc = PutDiagnosticError(400, 'schema_validation', 'unknown')
        exc.validation_details = summarize_server_validation(json.dumps({
            'errors': [{'path': '/body', 'errorCode': 'TYPE', 'message': 'PRIVATE_MESSAGE'}]
        }).encode())
        raise exc

    monkeypatch.setattr(exp, 'put_recipe', reject)
    args = SimpleNamespace(result=str(marker), variant='original', mode='dry-run')
    with pytest.raises(PutDiagnosticError):
        exp._run_online(args, 'uuid', baseline, sha, baseline, 'candidate-sha')
    receipt = (tmp_path / 'attempt.json.receipt.json').read_text()
    local = json.loads((tmp_path / 'attempt.json.local-errors.json').read_text())
    assert 'PRIVATE_MESSAGE' not in receipt
    assert local['errors'] == [{'path': '/body', 'errorCode': 'TYPE', 'message': 'PRIVATE_MESSAGE'}]
    assert 'local_full_errors' not in receipt
