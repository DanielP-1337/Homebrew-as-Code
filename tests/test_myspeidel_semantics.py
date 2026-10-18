"""Offline tests: numeric-only semantics; no MySpeidel network traffic."""
import json

import pytest

from homebrew_as_code.myspeidel import MySpeidelError
from homebrew_as_code.myspeidel_semantics import analyze_detail
from homebrew_as_code.myspeidel_semantics_cli import main

UUID = "12345678-1234-1234-1234-123456789abc"


class FakeClient:
    def __init__(self, token):
        self.fetches = 0

    def list_recipes(self, *, machine_size, include_public):
        return {"collection": [{"uuid": UUID, "public": 0, "machine_type": {"size": 20}}]}

    def get_recipe(self, uuid):
        self.fetches += 1
        return {"machine_type": {"size": 20}, "name": "PRIVATE", "uuid": uuid,
                "boil": {"boiling_duration": 60, "steps": [
                    {"duration": 15, "adds": {"hops": [{"amount": 12.5, "acid": 4.2,
                        "hop_uuid": "SECRET"}]}},
                    {"duration": 45, "adds": {"hops": []}}]},
                "mashing": {"adds": {"malts": [{"amount": 2500, "malt_uuid": "SECRET"}],
                                      "water": {"water_amount_start": 23}}},
                "rest": {"water_amount_addition": 5},
                "references": {"hops": {"SECRET": {"name": "PRIVATE"}}}}


def test_numeric_allowlist():
    data = analyze_detail(FakeClient("token").get_recipe(UUID))
    assert data["malt_amounts_raw"] == [2500]
    assert data["boil_steps"][0]["duration_raw"] == 15
    assert data["boil_steps"][0]["hops"][0]["amount_raw"] == 12.5
    dumped = json.dumps(data)
    for secret in ("PRIVATE", "SECRET", UUID, "hop_uuid", "malt_uuid"):
        assert secret not in dumped
    assert "UNVERIFIED" in dumped


def test_missing_values_not_guessed():
    data = analyze_detail({"boil": {"steps": [{"adds": {}}]}})
    assert data["boil_steps"][0]["duration_raw"] is None
    assert data["malt_amounts_raw"] == []


def test_bad_detail():
    with pytest.raises(MySpeidelError):
        analyze_detail(["not a recipe"])


def test_nonfinite_and_bool_filtered():
    data = analyze_detail({"boil": {"boiling_duration": True,
        "steps": [{"duration": float("nan"), "adds": {"hops": [{"amount": float("inf")}]}}]}})
    assert data["boil_duration_raw"] is None
    assert data["boil_steps"][0]["duration_raw"] is None
    assert data["boil_steps"][0]["hops"][0]["amount_raw"] is None


def _cli(monkeypatch, answers):
    fake = FakeClient("token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_semantics_cli.login", lambda u, p: "token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_semantics_cli.MySpeidelClient", lambda token: fake)
    monkeypatch.setattr("getpass.getpass", lambda _: "password")
    iterator = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))
    return fake


def test_no_consent_no_detail(monkeypatch, capsys):
    fake = _cli(monkeypatch, ["user", "1", "no"])
    assert main([]) == 0
    assert fake.fetches == 0
    assert "PRIVATE" not in capsys.readouterr().out


def test_valid_consent(monkeypatch, capsys):
    fake = _cli(monkeypatch, ["user", "1", "yes"])
    assert main([]) == 0
    assert fake.fetches == 1
    out = capsys.readouterr().out
    assert '"duration_raw": 15' in out and "SECRET" not in out


def test_bad_number_never_fetches(monkeypatch):
    fake = _cli(monkeypatch, ["user", "9"])
    assert main([]) == 1
    assert fake.fetches == 0
