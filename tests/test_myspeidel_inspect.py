"""Offline tests: no real MySpeidel credentials or network access."""
import json

import pytest

from homebrew_as_code.myspeidel import MySpeidelError
from homebrew_as_code.myspeidel_inspect import (
    inspect_recipe, local_recipe_inventory, private_recipes,
)
from homebrew_as_code.myspeidel_inspect_cli import main

UUID = "12345678-1234-1234-1234-123456789abc"


class FakeClient:
    def __init__(self):
        self.read_count = 0
        self.last_uuid = None

    def list_recipes(self, *, machine_size, include_public):
        assert machine_size == 20 and include_public is False
        return {"collection": [
            {"uuid": UUID, "public": 0, "machine_type": {"size": 20},
             "schema_version": 5, "content_version": 1},
            {"uuid": "other", "public": 1, "machine_type": {"size": 20}},
            {"uuid": "wrong", "public": 0, "machine_type": {"size": 50}},
        ]}

    def get_recipe(self, uuid):
        self.read_count += 1
        self.last_uuid = uuid
        return {"name": "private-name", "mashing": {"temperature": 60},
                "rest": {"steps": [{"temperature": 63, "duration": 20}]}}


def test_private_filter():
    assert len(private_recipes(FakeClient())) == 1


def test_detail_hides_private_values():
    client = FakeClient()
    selected = private_recipes(client)[0]
    output = inspect_recipe(client, selected)
    encoded = json.dumps(output)
    assert client.read_count == 1 and client.last_uuid == UUID
    assert UUID not in encoded and "private-name" not in encoded
    assert output["detail_structure"]["rest"]["steps"]["item_schema"]["duration"] == "number"


def test_wrong_machine_never_fetched():
    client = FakeClient()
    with pytest.raises(MySpeidelError):
        inspect_recipe(client, {"uuid": UUID, "public": 0, "machine_type": {"size": 50}})
    assert client.read_count == 0


def test_missing_collection_fails_closed():
    class Broken:
        def list_recipes(self, **kwargs):
            return {"recipes": []}
    with pytest.raises(MySpeidelError):
        private_recipes(Broken())


def test_local_inventory():
    inv = local_recipe_inventory("recipes/lebkuchen-zauber/recipe.yaml")
    assert inv["mash_step_count"] == 3
    assert inv["boil_addition_count"] == 7
    assert inv["mapping_status"].startswith("NOT_IMPLEMENTED")


def test_cancel_does_not_fetch(monkeypatch, capsys):
    monkeypatch.setattr("homebrew_as_code.myspeidel_inspect_cli.login", lambda u, p: "token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_inspect_cli.MySpeidelClient", lambda token: FakeClient())
    monkeypatch.setattr("getpass.getpass", lambda prompt: "password")
    answers = iter(["user", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert main([]) == 0
    assert "Cancelled" in capsys.readouterr().out


def test_invalid_selection_does_not_fetch(monkeypatch, capsys):
    client = FakeClient()
    monkeypatch.setattr("homebrew_as_code.myspeidel_inspect_cli.login", lambda u, p: "token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_inspect_cli.MySpeidelClient", lambda token: client)
    monkeypatch.setattr("getpass.getpass", lambda prompt: "password")
    answers = iter(["user", "999"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert main([]) == 1
    assert client.read_count == 0
    assert "ERROR" in capsys.readouterr().err
