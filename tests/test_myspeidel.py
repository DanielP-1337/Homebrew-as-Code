"""Network-free tests for the read-only client."""

import io
import json
import urllib.error

import pytest

from homebrew_as_code.myspeidel import MySpeidelClient, MySpeidelError, inspect_structure
from homebrew_as_code.myspeidel_cli import main


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self, count):
        return self.stream.read(count)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def test_list_only_get_and_bearer():
    captured = []

    def opener(request, timeout):
        captured.append(request)
        assert timeout == 15
        return FakeResponse({"collection": [{"uuid": 123, "name": "Private beer"}]})

    client = MySpeidelClient(token="fake-secret", opener=opener)
    assert client.list_recipes(machine_size=20)["collection"][0]["uuid"] == 123
    assert captured[0].get_method() == "GET"
    assert captured[0].get_header("Authorization") == "Bearer fake-secret"
    assert "size=20" in captured[0].full_url
    assert captured[0].full_url.startswith("https://api.cloud.myspeidel.com/v1.0/propfind/recipe?")


def test_get_numeric_uuid_only():
    client = MySpeidelClient(token="x", opener=lambda req, timeout: FakeResponse({"rest": {"steps": []}}))
    assert client.get_recipe("123e4567-e89b-12d3-a456-426614174000")["rest"]["steps"] == []
    for invalid in ("../auth", "abc", "123?x=1", "", "1/2", "123"):
        with pytest.raises(MySpeidelError):
            client.get_recipe(invalid)


def test_token_required(monkeypatch):
    monkeypatch.delenv("MYSPEIDEL_TOKEN", raising=False)
    with pytest.raises(MySpeidelError, match="missing"):
        MySpeidelClient()


def test_no_mutating_endpoints():
    client = MySpeidelClient(token="x")
    with pytest.raises(MySpeidelError, match="Disallowed"):
        client._get("/v1.0/auth/authentication")


def test_auth_errors_do_not_leak_body_or_token():
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "bad", {}, io.BytesIO(b"secret!"))

    with pytest.raises(MySpeidelError) as e:
        MySpeidelClient(token="private-value", opener=opener).list_recipes()
    assert "401" in str(e.value)
    assert "private-value" not in str(e.value)
    assert "secret!" not in str(e.value)


def test_structure_hides_values():
    result = inspect_structure({"username": "private", "items": [{"id": 5, "name": "secret"}]})
    assert "private" not in json.dumps(result)
    assert "secret" not in json.dumps(result)
    assert result["items"]["item_schema"]["id"] == "number"


def test_cli_invalid_id(monkeypatch, capsys):
    monkeypatch.setenv("MYSPEIDEL_TOKEN", "x")
    assert main(["get", "../invalid"]) == 1
    assert "ERROR" in capsys.readouterr().err
