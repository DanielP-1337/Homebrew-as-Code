"""Synthetic public fixtures only; original application exports stay in .local/."""
import copy
import json
import socket

import pytest
from jsonschema import Draft7Validator
from referencing.exceptions import NoSuchResource

from homebrew_as_code.beerjson_conformance import (
    SCHEMA_TARGET, _deny_retrieval, load_validator, validate_beerjson,
)
from homebrew_as_code.interoperability import inspect_document, main


def sample(version=1):
    return {"beerjson": {"version": version, "recipes": [{
        "name": "Synthetic conformance fixture", "type": "all grain", "author": "HBAC tests",
        "batch_size": {"unit": "l", "value": 10},
        "efficiency": {"brewhouse": {"unit": "%", "value": 65}},
        "ingredients": {"fermentable_additions": []},
    }]}}


def validate(document):
    return validate_beerjson(document, schema_target=SCHEMA_TARGET)


def test_offline_validation_preserves_document(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Network access attempted")
    monkeypatch.setattr(socket, "socket", fail)
    doc = sample()
    before = copy.deepcopy(doc)
    report = validate(doc)
    assert report["schema_valid"] and report["version_policy_match"]
    assert report["import_ready"] is False
    assert doc == before
    with pytest.raises(NoSuchResource):
        _deny_retrieval("https://example.invalid/schema.json")


@pytest.mark.parametrize("version", [2.06, 3, 999])
def test_schema_accepts_numeric_version_but_policy_does_not(version):
    report = validate(sample(version))
    assert report["schema_valid"] is True
    assert report["version_policy_match"] is False
    assert report["declared_version"] == version


@pytest.mark.parametrize("version", [True, "1", None])
def test_version_requires_number(version):
    report = validate(sample(version))
    assert not report["schema_valid"]
    assert not report["version_policy_match"]


def test_required_fields_and_unknown_fields():
    doc = sample()
    recipe = doc["beerjson"]["recipes"][0]
    del recipe["batch_size"]
    recipe["vendor_private_field"] = "secret"
    report = validate(doc)
    assert {e["keyword"] for e in report["errors"]} == {"required", "additionalProperties"}
    assert "secret" not in json.dumps(report)


@pytest.mark.parametrize("unit,value,valid", [("g", 11.5, True), ("kg", .0115, True),
                                            ("packet", 1, False), ("g", "11.5", False)])
def test_official_mass_type(unit, value, valid):
    validator, _ = load_validator()
    schema = {"$ref": "https://raw.githubusercontent.com/beerjson/beerjson/master/json/measureable_units.json#/definitions/MassType"}
    assert validator.evolve(schema=schema).is_valid({"unit": unit, "value": value}) is valid


def test_wrong_nested_unit_and_missing_mass_value():
    doc = sample()
    doc["beerjson"]["recipes"][0]["batch_size"]["unit"] = "kg"
    assert not validate(doc)["schema_valid"]
    validator, _ = load_validator()
    schema = {"$ref": "https://raw.githubusercontent.com/beerjson/beerjson/master/json/measureable_units.json#/definitions/MassType"}
    assert not validator.evolve(schema=schema).is_valid({"unit": "g"})


def test_unknown_schema_target_rejected():
    with pytest.raises(ValueError, match="Unsupported schema"):
        validate_beerjson(sample(), schema_target="main")


@pytest.mark.parametrize("content,expected", [
    (b'<RECIPES><RECIPE><VERSION>1</VERSION></RECIPE></RECIPES>', "beerxml"),
    (b'<BeerXML><version>2.01</version></BeerXML>', "beerxml_2_candidate"),
    (b'{"_versionId":"synthetic","fermentables":[],"yeasts":[]}', "brewfather_json_candidate"),
    (b'{}', "unknown"),
])
def test_format_probes_never_claim_schema_validation(content, expected):
    report = inspect_document(content, schema_target=SCHEMA_TARGET)
    assert report["format"] == expected
    assert report["schema_valid"] is None
    assert report["import_ready"] is False


@pytest.mark.parametrize("content", [b'{"beerjson":{},"beerjson":{}}', b'{"x":NaN}',
                                       b'<!DOCTYPE a><RECIPES/>', b'<broken>', b'not json'])
def test_malformed_or_ambiguous_documents_rejected(content):
    with pytest.raises(Exception):
        inspect_document(content, schema_target=SCHEMA_TARGET)


def test_cli_report_exit_status_and_no_overwrite(tmp_path):
    source, report = tmp_path / "input.json", tmp_path / "report.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    args = [str(source), "--schema-target", SCHEMA_TARGET, "--report", str(report)]
    assert main(args) == 0
    original = report.read_bytes()
    assert main(args) == 1
    assert report.read_bytes() == original
    report.unlink()
    source.write_text(json.dumps(sample(2.06)), encoding="utf-8")
    assert main(args) == 2
    assert json.loads(report.read_text())["inputs"][0]["schema_valid"] is True


def test_cli_missing_and_malformed_inputs_are_reported(tmp_path):
    malformed, report = tmp_path / "malformed.json", tmp_path / "report.json"
    malformed.write_text("{broken", encoding="utf-8")
    assert main([str(malformed), str(tmp_path / "missing"), "--schema-target", SCHEMA_TARGET,
                 "--report", str(report)]) == 2
    result = json.loads(report.read_text())
    assert all(r["format"] == "unreadable" for r in result["inputs"])
    assert "broken" not in report.read_text()


def test_cli_rejects_input_as_report(tmp_path):
    source = tmp_path / "input.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    original = source.read_bytes()
    assert main([str(source), "--schema-target", SCHEMA_TARGET, "--report", str(source)]) == 1
    assert source.read_bytes() == original


@pytest.mark.parametrize("line_endings", ["lf", "crlf", "mixed"])
def test_schema_bundle_checkout_line_endings(tmp_path, monkeypatch, line_endings):
    import shutil
    from pathlib import Path
    import homebrew_as_code.beerjson_conformance as conformance

    source = Path(__file__).resolve().parents[1] / "src/homebrew_as_code/schemas"
    shutil.copytree(source, tmp_path / "schemas")
    for path in (tmp_path / "schemas/beerjson_v1").iterdir():
        content = path.read_bytes().replace(b"\r\n", b"\n")
        if line_endings == "crlf":
            content = content.replace(b"\n", b"\r\n")
        elif line_endings == "mixed":
            content = content.replace(b"\n", b"\r\n", 1)
        path.write_bytes(content)
    monkeypatch.setattr(conformance, "files", lambda _: tmp_path)
    assert validate(sample())["schema_valid"] is True


@pytest.mark.parametrize("filename", ["LICENSE", "beer.json"])
def test_real_bundle_changes_still_fail_integrity(tmp_path, monkeypatch, filename):
    import shutil
    from pathlib import Path
    import homebrew_as_code.beerjson_conformance as conformance

    source = Path(__file__).resolve().parents[1] / "src/homebrew_as_code/schemas"
    shutil.copytree(source, tmp_path / "schemas")
    path = tmp_path / "schemas/beerjson_v1" / filename
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n") + b" ")
    monkeypatch.setattr(conformance, "files", lambda _: tmp_path)
    with pytest.raises(conformance.SchemaIntegrityError, match=filename):
        validate(sample())


def test_cli_reports_bundle_failure_as_command_failure(tmp_path, monkeypatch, capsys):
    import homebrew_as_code.beerjson_conformance as conformance

    def fail():
        raise conformance.SchemaIntegrityError("Vendored schema integrity failure: LICENSE")

    monkeypatch.setattr(conformance, "load_validator", fail)
    source, report = tmp_path / "input.json", tmp_path / "report.json"
    source.write_text(json.dumps(sample()), encoding="utf-8")
    assert main([str(source), "--schema-target", SCHEMA_TARGET, "--report", str(report)]) == 1
    assert not report.exists()
    assert "LICENSE" in capsys.readouterr().err
