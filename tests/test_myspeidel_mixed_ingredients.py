"""Read-only mixed ingredient evidence tests (0008b)."""
import copy
import json

import pytest

from homebrew_as_code.myspeidel import MySpeidelError
from homebrew_as_code.myspeidel_roundtrip import diagnose_boil_additions, compare_roundtrip


def fixture():
    return {
        "boil": {"boiling_duration": 60, "boiling_temperature": 100, "steps": [
            {"duration": 60, "adds": {"hops": [{"amount": 11, "acid": 5, "hop_uuid": "SECRET-HOP"}]}},
            {"duration": 20, "adds": {"hops": [{"amount": 7, "acid": 5}]}},
            {"duration": 5, "adds": {"hops": [{"amount": 5, "acid": 0, "ingredient_uuid": "SECRET-CINNAMON", "name": "SECRET-NAME"}]}},
        ]},
        "references": {"hops": {"SECRET-HOP": {}}, "ingredients": {"SECRET-CINNAMON": {}}},
    }


def test_mixed_additions_numeric_report_and_no_sensitive_data():
    raw = fixture()
    original = copy.deepcopy(raw)
    report = diagnose_boil_additions(raw)
    third = report["steps"][2]
    assert third["duration_raw"] == 5
    assert third["hops"]["count"] == 1
    assert third["hops"]["entries"][0]["amount_raw"] == 5
    assert third["hops"]["entries"][0]["acid_raw"] == 0
    assert third["hops"]["entries"][0]["reference_fields_present"]["ingredient_uuid"] is True
    assert third["ingredients"]["type"] == "absent"
    assert report["reference_counts"] == {"hops": 1, "ingredients": 1}
    encoded = json.dumps(report)
    assert "SECRET" not in encoded
    assert raw == original


def test_distinguish_hops_and_ingredients_containers():
    raw = fixture()
    raw["boil"]["steps"][2]["adds"] = {"ingredients": [{"amount": 5, "ingredient_uuid": "SECRET"}]}
    step = diagnose_boil_additions(raw)["steps"][2]
    assert step["hops"]["type"] == "absent"
    assert step["ingredients"]["count"] == 1


def test_malformed_and_bool_numeric_never_leaks():
    raw = fixture()
    raw["boil"]["steps"][0]["adds"]["hops"] = [None, {"amount": True, "acid": float("nan"), "uuid": "SECRET"}]
    entries = diagnose_boil_additions(raw)["steps"][0]["hops"]["entries"]
    assert entries[0] == {"shape": "non_object"}
    assert entries[1]["amount_raw"] is None
    assert entries[1]["acid_raw"] is None
    assert "SECRET" not in json.dumps(entries, allow_nan=False)


def test_invalid_steps_refused():
    with pytest.raises(MySpeidelError):
        diagnose_boil_additions({"boil": {"steps": "wrong"}})


def test_existing_report_includes_mixed_diagnostics_and_remains_blocked():
    report = compare_roundtrip(fixture(), 60, [60, 20, 5])
    assert report["upload_ready"] is False
    assert report["api_payload"] is None
    assert report["candidate_matches"]["api_values_equal_web_remaining_times"] is True
    assert report["boil_addition_diagnostics"]["steps"][2]["hops"]["entries"][0]["amount_raw"] == 5
    assert "SECRET" not in json.dumps(report)
