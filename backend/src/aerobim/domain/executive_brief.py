"""One-page executive brief for the customer-facing export.

Two-layer report: short summary first, evidence drill-down below.
Does not hide SKIPPED / NOT_VERIFIED / advisory. Not product accuracy.
Single-expert pilot review is not statistical validation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO, PRECISION_PUBLISHABLE
from aerobim.domain.finding_layer import classify_finding_layer, layer_counts
from aerobim.domain.review_projection import review_partition_of

CLAIM_BOUNDARY: Final = (
    "Operational brief for a named-expert review of issued findings. "
    "Not precision/recall. Not TZ >90%. Not customer SLA. "
    "Advisory and skipped checks stay visible. Checkpoint GO; customer_go false."
)


def _cap_status(capabilities: object, name: str) -> str:
    if not isinstance(capabilities, Mapping):
        return "not_verified"
    payload = capabilities.get(name)
    if isinstance(payload, Mapping):
        status = payload.get("status")
        return str(getattr(status, "value", status) or "not_verified").lower()
    if payload is not None:
        return str(getattr(payload, "value", payload)).lower()
    return "not_verified"


_NEGATIVE_CAP_STATUSES: Final = frozenset(
    {"skipped", "not_verified", "missing", "failed", "not_implemented"}
)
_NEGATIVE_STATUS_ALIASES: Final = frozenset({"not_checked", "not-checked", "skipped"})


def _coverage_not_checked(coverage: object) -> int:
    if not isinstance(coverage, Mapping):
        return 0
    count = 0
    for gap in coverage.get("tz_gaps") or ():
        if isinstance(gap, Mapping):
            status = str(gap.get("status") or "").casefold()
            if status in _NEGATIVE_STATUS_ALIASES:
                count += 1
    for row in coverage.get("sources") or ():
        if not isinstance(row, Mapping):
            continue
        ops = row.get("operator_status") or row.get("families") or {}
        if not isinstance(ops, Mapping):
            continue
        for status in ops.values():
            if str(status).casefold() in _NEGATIVE_STATUS_ALIASES:
                count += 1
    return count


def _negative_capabilities(capabilities: object) -> list[dict[str, str]]:
    if not isinstance(capabilities, Mapping):
        return []
    rows: list[dict[str, str]] = []
    for name, payload in capabilities.items():
        status = _cap_status({name: payload}, name)
        if status in _NEGATIVE_CAP_STATUSES:
            rows.append({"name": str(name), "status": status})
    return rows


def executive_brief(data: Mapping[str, Any]) -> dict[str, Any]:
    issues = [item for item in (data.get("issues") or ()) if isinstance(item, Mapping)]
    counts = layer_counts(issues)
    pack = [
        item
        for item in issues
        if classify_finding_layer(item) == "pack_finding"
        and review_partition_of(item) != "rejected"
    ]
    confirmed = sum(1 for item in pack if review_partition_of(item) == "confirmed")
    edited = sum(1 for item in pack if review_partition_of(item) == "edited")
    rejected = sum(1 for item in issues if review_partition_of(item) == "rejected")
    unresolved_review = sum(1 for item in pack if review_partition_of(item) == "untouched")
    caps = data.get("capabilities")
    mep = _cap_status(caps, "mep_system_clash")
    dwg = _cap_status(caps, "dwg_dxf")
    calc_ok = _cap_status(caps, "calculation_correctness")
    passport = data.get("run_passport") if isinstance(data.get("run_passport"), Mapping) else {}
    stages = passport.get("stages") if isinstance(passport, Mapping) else ()
    total_ms = 0
    if isinstance(stages, Sequence):
        for stage in stages:
            if isinstance(stage, Mapping) and stage.get("name") == "report":
                total_ms = int(stage.get("cumulative_ms") or 0)
            elif isinstance(stage, Mapping):
                total_ms = max(total_ms, int(stage.get("cumulative_ms") or 0))
    calc_raw = data.get("calculation_section")
    calc = calc_raw if isinstance(calc_raw, Mapping) else {}
    calc_rows = [row for row in (calc.get("rows") or ()) if isinstance(row, Mapping)]
    return {
        "schema_version": "1.0.0",
        "artifact_type": "executive_brief",
        "review_mode": "single_expert_pilot_review",
        "is_accuracy": False,
        "is_sla": False,
        "precision_claim_publishable": PRECISION_PUBLISHABLE,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "claim_boundary": CLAIM_BOUNDARY,
        "pack_findings": len(pack),
        "confirmed": confirmed,
        "edited": edited,
        "rejected": rejected,
        "unresolved_review": unresolved_review,
        "advisory_candidates": counts["advisory_candidate"],
        "coverage_notes": counts["coverage_note"],
        "service_records": counts["service_record"],
        "machine_records": len(issues),
        "coverage_not_checked": _coverage_not_checked(data.get("coverage")),
        "mep_system_clash": mep,
        "native_dwg": dwg,
        "calculation_correctness": calc_ok,
        "calculation_rows": [
            {"id": row.get("id"), "status": row.get("status")} for row in calc_rows
        ],
        "run_duration_ms": total_ms or None,
        "negative_capabilities": _negative_capabilities(caps),
        "hides_negative": False,
    }
