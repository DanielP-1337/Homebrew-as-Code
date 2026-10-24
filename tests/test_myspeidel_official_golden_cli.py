"""Offline-only tests for the official recipe copy guard."""
from unittest.mock import patch

import pytest

from homebrew_as_code.myspeidel_official_golden_cli import validate_copy, main


def _backup(name='Weizenbier 38° – API Roundtrip Test'):
    return ('00000000-0000-4000-8000-000000000001',
            {'name': name, 'uuid': '00000000-0000-4000-8000-000000000001',
             'public': 0, 'machine_type': {'size': 20}}, 'verified-digest')


def test_requires_explicit_attestation():
    with pytest.raises(ValueError, match='confirm-private-copy'):
        validate_copy('.local/golden.json', False)


def test_rejects_unrelated_recipe():
    with patch('homebrew_as_code.myspeidel_official_golden_cli.private_file', return_value='path'), \
         patch('homebrew_as_code.myspeidel_official_golden_cli.read_backup', return_value=_backup('Other recipe')):
        with pytest.raises(ValueError, match='Weizenbier'):
            validate_copy('.local/golden.json', True)


def test_prepare_never_logs_in_or_calls_put(tmp_path):
    uuid, recipe, _ = _backup()
    with patch('homebrew_as_code.myspeidel_official_golden_cli.validate_copy', return_value=(uuid, recipe, 'hash')), \
         patch('homebrew_as_code.myspeidel_official_golden_cli.private_file', return_value=tmp_path / 'out.json'), \
         patch('homebrew_as_code.myspeidel_official_golden_cli.write_new') as writer, \
         patch('homebrew_as_code.myspeidel_put_experiments._run_online') as network:
        assert main(['--backup', '.local/b.json', '--mode', 'prepare', '--result', '.local/out.json',
                     '--confirm-private-copy']) == 0
        assert writer.call_args.args[1]['unchanged_payload'] is True
        network.assert_not_called()


def test_apply_requires_second_write_switch():
    uuid, recipe, _ = _backup()
    with patch('homebrew_as_code.myspeidel_official_golden_cli.validate_copy', return_value=(uuid, recipe, 'hash')), \
         patch('homebrew_as_code.myspeidel_put_experiments._run_online') as network:
        assert main(['--backup', '.local/b.json', '--mode', 'apply', '--result', '.local/out.json',
                     '--confirm-private-copy']) == 1
        network.assert_not_called()
