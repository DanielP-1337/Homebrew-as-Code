"""Offline tests of official password authentication and privacy safeguards."""
import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from homebrew_as_code.myspeidel import MySpeidelClient, MySpeidelError
from homebrew_as_code.myspeidel_auth import login


class Response:
    def __init__(self, payload):
        self.data = io.BytesIO(json.dumps(payload).encode())
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.data.read(n)


def test_login_official_payload_and_token():
    def opener(request, timeout):
        assert timeout == 15
        assert request.get_method() == "POST"
        assert request.full_url == "https://api.cloud.myspeidel.com/v1.0/auth/authentication"
        assert json.loads(request.data) == {"username": "alice", "pass": "private"}
        assert "Authorization" not in request.headers
        return Response({"token": "session-token", "userid": 9})
    assert login("alice", "private", opener=opener) == "session-token"


def test_auth_error_redacts_password():
    def opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 401, "private", {}, io.BytesIO(b"private"))
    with pytest.raises(MySpeidelError) as exc:
        login("alice", "private", opener=opener)
    assert "private" not in str(exc.value)
    assert "401" in str(exc.value)


def test_password_missing_rejected():
    with pytest.raises(MySpeidelError):
        login("alice", "")


def test_recipe_query_names_and_uuid():
    captured=[]
    def opener(request, timeout):
        captured.append(request)
        return Response({"collection": []})
    client=MySpeidelClient(token="session-token",opener=opener)
    client.list_recipes(machine_size=20)
    assert "size=20" in captured[0].full_url
    assert "includePublic=0" in captured[0].full_url
    assert "machineSize=" not in captured[0].full_url
    uuid="123e4567-e89b-12d3-a456-426614174000"
    client.get_recipe(uuid)
    assert captured[-1].full_url.endswith("/v1.0/recipe/"+uuid)
