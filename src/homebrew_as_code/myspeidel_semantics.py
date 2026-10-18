"""Read-only, numeric-only evidence for mapping MySpeidel recipe fields.

The API's field names alone do not establish amount units or the meaning of
boil.step.duration. This module intentionally makes no such inference.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

from .myspeidel import MySpeidelError


def _number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _dict(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def _array(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def analyze_detail(detail: Any) -> dict[str, Any]:
    """Report allowlisted numeric values; no names, IDs, UUIDs or raw JSON.

    Output can still reveal confidential recipe quantities, so CLI requires
    explicit confirmation before displaying it. No unit claims are made.
    """
    if not isinstance(detail, dict):
        raise MySpeidelError("Unexpected recipe detail structure")
    mash = _dict(detail.get("mashing"))
    malts = _array(_dict(mash.get("adds")).get("malts"))
    boil = _dict(detail.get("boil"))
    boil_steps = _array(boil.get("steps"))
    results: list[dict[str, Any]] = []
    for index, step in enumerate(boil_steps):
        entry = _dict(step)
        hops = _array(_dict(entry.get("adds")).get("hops"))
        results.append({
            "index": index,
            "duration_raw": _number(entry.get("duration")),
            "hops": [{"amount_raw": _number(_dict(h).get("amount")),
                      "alpha_acid_raw": _number(_dict(h).get("acid"))} for h in hops],
        })
    references = _dict(detail.get("references"))
    return {
        "evidence_status": "RAW_NUMERIC_VALUES_ONLY_UNITS_UNVERIFIED",
        "boil_duration_raw": _number(boil.get("boiling_duration")),
        "boil_steps": results,
        "malt_amounts_raw": [_number(_dict(m).get("amount")) for m in malts],
        "mash_water_amount_raw": _number(_dict(_dict(mash.get("adds")).get("water")).get("water_amount_start")),
        "sparge_water_amount_raw": _number(_dict(detail.get("rest")).get("water_amount_addition")),
        "reference_counts": {kind: len(_dict(references.get(kind)))
                             for kind in ("hops", "malts", "ingredients", "water_types", "yeasts")},
        "unresolved": [
            "Determine whether boil.steps.duration means time remaining, elapsed time, or step duration from a known recipe.",
            "Confirm units for hop/malt amount and acid against documented API conventions or known recipe entries.",
            "Resolve ingredient reference UUIDs separately before constructing an upload payload.",
        ],
    }
