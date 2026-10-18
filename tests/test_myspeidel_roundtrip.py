"""All tests run offline and prove the read-only comparison privacy boundary."""
import json

import pytest

from homebrew_as_code.myspeidel import MySpeidelError
from homebrew_as_code.myspeidel_roundtrip import compare_roundtrip, parse_web_times
from homebrew_as_code.myspeidel_roundtrip_cli import main

UUID = "12345678-1234-1234-1234-123456789abc"


def detail():
    return {"uuid": UUID, "name": "PRIVATE SECRET", "machine_type": {"size": 20},
            "boil": {"boiling_duration": 60, "steps": [
                {"duration": 40, "adds": {"hops": [{"amount": 11, "hop_uuid": UUID}]}},
                {"duration": 20, "adds": {"hops": [{"amount": 7}]}}]},
            "references": {"hops": {UUID: {"name": "PRIVATE SECRET"}}}}


def test_web_times():
    assert parse_web_times("60,20", 60) == [60, 20]


@pytest.mark.parametrize("raw", ["", "20,60", "60,60", "61,20", "-2,1", "nan", "inf", "20,x"])
def test_reject_bad_times(raw):
    with pytest.raises(MySpeidelError):
        parse_web_times(raw, 60)


def test_comparison_private_and_blocked():
    result = compare_roundtrip(detail(), 60, [60, 20])
    assert result["upload_ready"] is False
    assert result["api_payload"] is None
    assert result["api_steps_sum_to_total"] is True
    assert result["candidate_matches"]["api_values_equal_web_remaining_times"] is False
    assert result["candidate_matches"]["api_spans_end_at_web_hop_events"] is False
    serial = json.dumps(result)
    # Reference field *labels* are diagnostic schema metadata, not secret values.
    # Never include identifier values or private recipe/ingredient names.
    for secret in ("PRIVATE", UUID, "PRIVATE SECRET"):
        assert secret not in serial
    references = result["boil_addition_diagnostics"]["steps"][0]["hops"]["entries"][0]["reference_fields_present"]
    assert references == {"uuid": False, "hop_uuid": True, "ingredient_uuid": False}
    assert all(isinstance(value, bool) for value in references.values())


def test_unverified_empty_steps():
    report = compare_roundtrip({"boil": {"boiling_duration": 60, "steps": []}}, 60, [60])
    assert report["api_steps_sum_to_total"] is None
    assert all(x is None for x in report["candidate_matches"].values())


def test_unequal_number_of_steps_is_unknown():
    report = compare_roundtrip(detail(), 60, [20])
    assert all(x is None for x in report["candidate_matches"].values())


class FakeClient:
    def __init__(self, token):
        self.fetches = 0
    def list_recipes(self, *, machine_size, include_public):
        return {"collection": [{"uuid": UUID, "public": 0, "machine_type": {"size": 20},
                                "name": "Private Weizen 38°", "created_on": "2026-10-18T14:23:00"}]}
    def get_recipe(self, uuid):
        self.fetches += 1
        return detail()


def setup_cli(monkeypatch, responses):
    fake = FakeClient("token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_roundtrip_cli.login", lambda u, p: "token")
    monkeypatch.setattr("homebrew_as_code.myspeidel_roundtrip_cli.MySpeidelClient", lambda token: fake)
    monkeypatch.setattr("getpass.getpass", lambda _: "secret")
    iterator = iter(responses)
    monkeypatch.setattr("builtins.input", lambda _: next(iterator))
    return fake


def test_no_consent_no_get(monkeypatch):
    fake = setup_cli(monkeypatch, ["user", "no", "1", "60", "60,20", "no"])
    assert main([]) == 0
    assert fake.fetches == 0


def test_get_only_numeric(monkeypatch, capsys):
    fake = setup_cli(monkeypatch, ["user", "no", "1", "60", "60,20", "yes"])
    assert main([]) == 0
    assert fake.fetches == 1
    output = capsys.readouterr().out
    assert '"api_total_min": 60' in output
    assert UUID not in output and "PRIVATE SECRET" not in output


def test_bad_selection_no_get(monkeypatch):
    fake = setup_cli(monkeypatch, ["user", "no", "99"])
    assert main([]) == 1
    assert fake.fetches == 0


def test_names_hidden_by_default(monkeypatch, capsys):
    setup_cli(monkeypatch, ["user", "", ""])
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "Private Weizen" not in out
    assert "2026-10-18" not in out
    assert "  1\n" in out


def test_explicit_opt_in_shows_name_and_date(monkeypatch, capsys):
    setup_cli(monkeypatch, ["user", "yes", ""])
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "1  Private Weizen 38°  [2026-10-18]" in out
    assert UUID not in out


def test_other_answer_does_not_reveal(monkeypatch, capsys):
    setup_cli(monkeypatch, ["user", "YES", ""])
    assert main([]) == 0
    assert "Private Weizen" not in capsys.readouterr().out


def test_metadata_is_terminal_safe():
    from homebrew_as_code.myspeidel_roundtrip_cli import _display_meta, _creation_date
    assert _display_meta("A\nB\x1b[31m\tC") == "A B [31m C"
    assert _display_meta(None) == "(unknown)"
    assert _creation_date({"created_on": "not-a-date\nPRIVATE"}) == "(unknown)"
    assert _creation_date({"created_on": "2026-10-18T10:12:00"}) == "2026-10-18"
