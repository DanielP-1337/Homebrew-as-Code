"""Credential manager is opt-in and does not touch networking or files."""
import pytest

from homebrew_as_code import myspeidel_credentials as creds
from homebrew_as_code import myspeidel_credentials_cli as cli


def test_nonwindows_fails_closed(monkeypatch):
    monkeypatch.setattr(creds.sys, 'platform', 'linux')
    with pytest.raises(creds.CredentialStoreError):
        creds.load_credentials()
    with pytest.raises(creds.CredentialStoreError):
        creds.save_credentials('test', 'secret')


def test_saved_credentials_used_without_interactive_prompts(monkeypatch):
    monkeypatch.setattr(creds, 'load_credentials', lambda: ('user', 'password'))
    monkeypatch.setattr('builtins.input', lambda _: pytest.fail('Unexpected input prompt'))
    assert creds.prompt_credentials() == ('user', 'password')


def test_absent_credentials_use_hidden_prompt(monkeypatch):
    monkeypatch.setattr(creds, 'load_credentials', lambda: None)
    monkeypatch.setattr('builtins.input', lambda _: 'person@example.test')
    monkeypatch.setattr(creds.getpass, 'getpass', lambda _: 'password')
    assert creds.prompt_credentials() == ('person@example.test', 'password')


def test_setup_requires_consent_and_status_never_discloses_secret(monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda message: 'no' if '[yes/NO]' in message else 'user')
    monkeypatch.setattr(cli.getpass, 'getpass', lambda _: 'top-secret')
    monkeypatch.setattr(cli, 'save_credentials', lambda *args: pytest.fail('should not save'))
    assert cli.main(['setup']) == 0
    assert 'top-secret' not in capsys.readouterr().out
    monkeypatch.setattr(cli, 'load_credentials', lambda: ('user', 'top-secret'))
    assert cli.main(['status']) == 0
    output = capsys.readouterr().out
    assert 'configured' in output and 'top-secret' not in output and 'user' not in output


def test_clear_requires_consent(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: 'no')
    monkeypatch.setattr(cli, 'clear_credentials', lambda: pytest.fail('should not delete'))
    assert cli.main(['clear']) == 0
