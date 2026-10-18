"""Compare manually entered web-form hop timings with GET-only API evidence.

No UUID, name, credential, raw recipe or personal metadata is returned.
The possible timing interpretations are hypotheses, not an API contract.
"""
from __future__ import annotations

from math import isfinite
from collections.abc import Mapping
from typing import Any

from .myspeidel import MySpeidelError
from .myspeidel_semantics import analyze_detail


def _valid_positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) and value > 0


def parse_web_times(raw: str, total: float) -> list[float]:
    """Read a descending list of manually verified minutes-before-end values."""
    try:
        values = [float(piece.strip()) for piece in raw.split(",")]
    except ValueError:
        raise MySpeidelError("Invalid web-form time list") from None
    if not values or not _valid_positive(total) or any(not _valid_positive(v) or v > total for v in values):
        raise MySpeidelError("Web-form times must be within (0, total]")
    if any(a <= b for a, b in zip(values, values[1:])):
        raise MySpeidelError("Web-form times must be strictly descending")
    return values


def compare_roundtrip(detail: dict[str, Any], web_total: float, web_times: list[float]) -> dict[str, Any]:
    """Compare numeric evidence only. Never infer a definitive semantics flag."""
    if not isinstance(detail, dict) or not _valid_positive(web_total):
        raise MySpeidelError("Invalid recipe detail or total")
    if not isinstance(web_times, list) or not web_times or any(not _valid_positive(t) or t > web_total for t in web_times):
        raise MySpeidelError("Invalid web-form times")
    if any(a <= b for a, b in zip(web_times, web_times[1:])):
        raise MySpeidelError("Web-form times must be descending")
    evidence = analyze_detail(detail)
    api_total = evidence["boil_duration_raw"]
    durations = [step["duration_raw"] for step in evidence["boil_steps"]]
    valid = all(_valid_positive(x) for x in durations) and len(durations) > 0
    # Candidates have explicit definitions: remaining time vs elapsed time vs
    # consecutive spans. Even a matching candidate is NOT proof of semantics.
    cumulative = []
    if valid:
        elapsed = 0
        for span in durations:
            elapsed += span
            cumulative.append(elapsed)
    candidates: dict[str, bool | None] = {
        "api_values_equal_web_remaining_times": None,
        "api_values_equal_web_elapsed_times": None,
        "api_spans_end_at_web_hop_events": None,
    }
    if valid and len(durations) == len(web_times):
        candidates["api_values_equal_web_remaining_times"] = _close_lists(durations, web_times)
        candidates["api_values_equal_web_elapsed_times"] = _close_lists(durations, [web_total - t for t in web_times])
        candidates["api_spans_end_at_web_hop_events"] = _close_lists(cumulative, [web_total - t for t in web_times])
    diagnostic = diagnose_boil_additions(detail)
    return {
        "format": "homebrew-as-code/myspeidel-roundtrip-evidence-v1",
        "source": "manual_web_form_vs_get_only_api",
        "upload_ready": False,
        "api_payload": None,
        "web_total_min": web_total,
        "api_total_min": api_total,
        "totals_match": _close(api_total, web_total),
        "web_hops_minutes_before_end": web_times,
        "api_boiling_step_durations_raw": durations,
        "api_step_hop_counts": [len(step["hops"]) for step in evidence["boil_steps"]],
        "boil_addition_diagnostics": diagnostic,
        "api_steps_sum_to_total": _close(sum(durations), api_total) if valid else None,
        "candidate_matches": candidates,
        "interpretation": "UNVERIFIED: candidate matches are only evidence, not a writer contract",
        "required_followup": "Check API step boundaries, extra no-hop steps and multiple test recipes before conversion",
    }


def _close(a: Any, b: Any) -> bool | None:
    if not _valid_positive(a) or not _valid_positive(b):
        return None
    return abs(a - b) <= 1e-6


def _close_lists(a: list[float], b: list[float]) -> bool:
    return len(a) == len(b) and all(abs(x - y) <= 1e-6 for x, y in zip(a, b))


def _safe_number(value: Any) -> float | int | None:
    """Return only finite numeric evidence, never strings/IDs or booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        return None
    return value


def _addition_entries(value: Any) -> dict[str, Any]:
    """Summarize known numerical fields without reproducing API objects."""
    if not isinstance(value, list):
        return {"present": value is not None, "type": "unexpected" if value is not None else "absent", "count": None, "entries": []}
    entries = []
    for item in value:
        if not isinstance(item, Mapping):
            entries.append({"shape": "non_object"})
            continue
        amount = _safe_number(item.get("amount"))
        acid = _safe_number(item.get("acid"))
        entries.append({
            "amount_raw": amount,
            "acid_raw": acid,
            "nonzero_amount": amount > 0 if amount is not None else None,
            "reference_fields_present": {key: isinstance(item.get(key), str) and bool(item[key])
                                         for key in ("uuid", "hop_uuid", "ingredient_uuid")},
        })
    return {"present": True, "type": "array", "count": len(value), "entries": entries}


def diagnose_boil_additions(detail: Mapping[str, Any]) -> dict[str, Any]:
    """Read-only, allowlisted shape evidence for hops vs non-hop additions.

    API collection names do NOT prove the ingredient's botanical type.
    No names, reference values, raw records, tokens, or identifiers are emitted.
    """
    boil = detail.get("boil")
    boil = boil if isinstance(boil, Mapping) else {}
    raw_steps = boil.get("steps")
    if not isinstance(raw_steps, list):
        raise MySpeidelError("Missing or invalid API boil steps")
    output = []
    for index, raw_step in enumerate(raw_steps):
        step = raw_step if isinstance(raw_step, Mapping) else {}
        adds = step.get("adds")
        adds = adds if isinstance(adds, Mapping) else {}
        output.append({
            "index": index,
            "duration_raw": _safe_number(step.get("duration")),
            "hops": _addition_entries(adds.get("hops")),
            "ingredients": _addition_entries(adds.get("ingredients")),
            "other_adds_keys_present": sorted(key for key in adds
                                              if isinstance(key, str) and key in ("malts", "yeasts", "water")),
        })
    references = detail.get("references")
    references = references if isinstance(references, Mapping) else {}
    return {
        "boiling_temperature_raw": _safe_number(boil.get("boiling_temperature")),
        "steps": output,
        "reference_counts": {key: len(references[key]) if isinstance(references.get(key), Mapping) else None
                             for key in ("hops", "ingredients")},
        "note": "API container type is not proof of ingredient category; compare with web editor",
    }
