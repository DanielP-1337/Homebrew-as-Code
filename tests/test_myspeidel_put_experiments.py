"""No-network safety and variant unit tests for 0019q."""
import copy
import pytest

from homebrew_as_code.myspeidel_put_experiments import make_variant


@pytest.fixture
def recipe():
    return {'references': {'water_types': {'SECRET_A': {'name': None, 'uuid': 'A'}},
                           'hops': {'SECRET_B': {'name': None, 'uuid': 'B'},
                                    'SECRET_C': {'name': 'Existing'}}},
            'other': {'name': None}}


@pytest.mark.parametrize('variant', ('original', 'omit-null-names', 'empty-string-names'))
def test_variants_preserve_input(recipe, variant):
    snapshot = copy.deepcopy(recipe)
    output, changes = make_variant(recipe, variant)
    assert recipe == snapshot
    assert output is not recipe
    assert output['other'] == {'name': None}
    assert set(output['references']['hops']) == {'SECRET_B', 'SECRET_C'}
    assert output['references']['hops']['SECRET_C']['name'] == 'Existing'
    assert changes == ({'water_types': 0, 'hops': 0} if variant == 'original'
                       else {'water_types': 1, 'hops': 1})
    if variant == 'omit-null-names':
        assert 'name' not in output['references']['water_types']['SECRET_A']
        assert 'name' not in output['references']['hops']['SECRET_B']
    elif variant == 'empty-string-names':
        assert output['references']['water_types']['SECRET_A']['name'] == ''
        assert output['references']['hops']['SECRET_B']['name'] == ''


def test_no_null_names_is_not_an_experiment(recipe):
    recipe['references']['water_types']['SECRET_A']['name'] = 'Water'
    recipe['references']['hops']['SECRET_B']['name'] = 'Hop'
    with pytest.raises(ValueError, match='No matching null names'):
        make_variant(recipe, 'omit-null-names')


def test_bad_shapes_fail_closed(recipe):
    recipe['references']['hops'] = []
    with pytest.raises(ValueError, match='reference category'):
        make_variant(recipe, 'empty-string-names')


def test_put_error_persisted_without_private_details(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    from homebrew_as_code import myspeidel_put_experiments as exp
    from homebrew_as_code.myspeidel_put_roundtrip import PutDiagnosticError
    import homebrew_as_code.myspeidel_put_roundtrip_cli as cli

    recipe = {'public': 0, 'name': 'test'}
    baseline_sha = exp.digest(recipe)
    marker = tmp_path / 'attempt.json'
    monkeypatch.setattr(exp, 'private_file', lambda value: marker)
    monkeypatch.setattr(exp, '_current', lambda client, uuid: recipe)
    monkeypatch.setattr(cli, '_login', lambda: ('fake-token', object()))
    monkeypatch.setattr('builtins.input', lambda prompt: 'DRY RUN EXPERIMENT')
    def reject(*a, **kw):
        raise PutDiagnosticError(400, 'schema_validation', 'references', ('PRIVATE_KEY',))
    monkeypatch.setattr(exp, 'put_recipe', reject)
    args = SimpleNamespace(result=str(marker), variant='omit-null-names', mode='dry-run')
    with pytest.raises(PutDiagnosticError):
        exp._run_online(args, 'private-id', recipe, baseline_sha, recipe, 'variant-digest')
    assert json.loads(marker.read_text())['phase'] == 'attempt_started'
    receipt = json.loads((tmp_path / 'attempt.json.receipt.json').read_text())
    assert receipt['http_status'] == 400
    assert receipt['error_type'] == 'schema_validation'
    assert receipt['error_location'] == 'references'
    assert receipt['server_state'] == 'baseline_match'
    assert receipt['phase'] == 'put_rejected'
    assert 'PRIVATE_KEY' not in json.dumps(receipt)


def test_preflight_denial_has_receipt_no_put(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace
    from homebrew_as_code import myspeidel_put_experiments as exp
    import homebrew_as_code.myspeidel_put_roundtrip_cli as cli
    recipe = {'public': 0}
    marker = tmp_path / 'attempt.json'
    monkeypatch.setattr(exp, 'private_file', lambda value: marker)
    monkeypatch.setattr(exp, '_current', lambda client, uuid: recipe)
    monkeypatch.setattr(cli, '_login', lambda: ('fake-token', object()))
    monkeypatch.setattr('builtins.input', lambda prompt: 'NO')
    monkeypatch.setattr(exp, 'put_recipe', lambda *a, **kw: pytest.fail('PUT sent'))
    args = SimpleNamespace(result=str(marker), variant='original', mode='dry-run')
    with pytest.raises(ValueError, match='Consent not given'):
        exp._run_online(args, 'private-id', recipe, exp.digest(recipe), recipe, exp.digest(recipe))
    receipt = json.loads((tmp_path / 'attempt.json.receipt.json').read_text())
    assert receipt['put_outcome'] == 'not_sent'
    assert receipt['server_state'] == 'not_checked'
