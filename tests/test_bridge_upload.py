from unittest.mock import patch

from homebrew_as_code.bridge_upload import main


def test_check_only_never_uploads(monkeypatch):
    monkeypatch.setenv('HA_TOKEN', 'test')
    with patch('homebrew_as_code.bridge_upload.call_action', return_value={'ready_for_upload': True}) as call:
        assert main(['recipes/lebkuchen-zauber/recipe.yaml', '--ha-url', 'https://ha.invalid']) == 0
    assert [c.args[2] for c in call.call_args_list] == ['recipe_upload_readiness']


def test_upload_tracks_specific_job(monkeypatch, tmp_path):
    monkeypatch.setenv('HA_TOKEN', 'test')
    with patch('homebrew_as_code.bridge_upload.call_action', side_effect=[
        {'ready_for_upload': True}, {'job_id': 'abc', 'result': 'queued'},
        {'job_id': 'abc', 'result': 'confirmed', 'content_verification': 'not_available'},
    ]) as call, patch('homebrew_as_code.bridge_upload.time.sleep'):
        assert main(['recipes/lebkuchen-zauber/recipe.yaml', '--ha-url', 'https://ha.invalid',
                     '--replace-all', '--job-file', str(tmp_path / 'job.json')]) == 0
    assert call.call_args.args[3] == {'job_id': 'abc'}
    assert (tmp_path / 'job.json').exists()


def test_lost_post_is_not_repeated(monkeypatch, tmp_path):
    monkeypatch.setenv('HA_TOKEN', 'test')
    with patch('homebrew_as_code.bridge_upload.call_action', side_effect=[
        {'ready_for_upload': True}, TimeoutError('lost response'),
    ]) as call:
        assert main(['recipes/lebkuchen-zauber/recipe.yaml', '--ha-url', 'https://ha.invalid',
                     '--replace-all', '--job-file', str(tmp_path / 'job.json')]) == 1
    assert call.call_count == 2
