"""TR-67 spec vs schedule vs model quantities. Not estimate QTO.

Customer answers 25.08 п. 2.1.3 call volume mismatch a logical collision.
That is a quantity triple, not IfcClash geometry and not model-to-estimate.
Missing any of the three sources is fail-closed (SOURCE_MISSING), not MATCH.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.quantity import parse_localized_number, parse_quantity, si_compare

CLAIM_BOUNDARY: Final = (
    "Fixture three-way declared quantities (specification, drawing schedule, "
    "BIM). Not model-to-estimate volumes. Not a customer pack. Not geometry "
    "clash. Checkpoint GO "
    "(regulatory_measurement_mvp; customer_go false). closes_rt001/002/003=false."
)
_NUMERIC_EPS: Final = 1e-3


@dataclass(frozen=True)
class SpecVolumeLine:
    """One specification line with three declared quantities."""

    line_id: str
    spec_qty: str | None
    schedule_qty: str | None
    model_qty: str | None
    unit: str


@dataclass(frozen=True)
class SpecVolumeLineResult:
    line_id: str
    outcome: Literal["MATCH", "MISMATCH", "SOURCE_MISSING"]
    finding_kind: str | None
    spec_qty: str | None
    schedule_qty: str | None
    model_qty: str | None
    unit: str


@dataclass(frozen=True)
class SpecVolumeCompareResult:
    lines: tuple[SpecVolumeLineResult, ...]
    all_match: bool
    checkpoint: str
    closes_rt001: bool
    closes_rt002: bool
    closes_rt003: bool
    claim_boundary: str


def _qty_match(left: str, right: str, unit: str) -> bool:
    left_n = parse_localized_number(left)
    right_n = parse_localized_number(right)
    if left_n is not None and right_n is not None:
        left_q = parse_quantity(left_n, unit or "1")
        right_q = parse_quantity(right_n, unit or "1")
        if left_q.si_value is not None and right_q.si_value is not None:
            return si_compare(left_q, right_q, epsilon=_NUMERIC_EPS)
        return abs(left_n - right_n) <= _NUMERIC_EPS
    return left.strip() == right.strip()


def compare_spec_volumes(lines: Sequence[SpecVolumeLine]) -> SpecVolumeCompareResult:
    """Compare specification, schedule, and model quantities per line."""

    results: list[SpecVolumeLineResult] = []
    for line in lines:
        key = line.line_id.strip()
        unit = line.unit.strip()
        sources = (line.spec_qty, line.schedule_qty, line.model_qty)
        if any(item is None or not str(item).strip() for item in sources):
            outcome: Literal["MATCH", "MISMATCH", "SOURCE_MISSING"] = "SOURCE_MISSING"
            kind: str | None = None
        else:
            spec_s = str(line.spec_qty)
            sched_s = str(line.schedule_qty)
            model_s = str(line.model_qty)
            if _qty_match(spec_s, sched_s, unit) and _qty_match(spec_s, model_s, unit):
                outcome = "MATCH"
                kind = None
            else:
                outcome = "MISMATCH"
                kind = "logical_collision"
        results.append(
            SpecVolumeLineResult(
                line_id=key,
                outcome=outcome,
                finding_kind=kind,
                spec_qty=line.spec_qty,
                schedule_qty=line.schedule_qty,
                model_qty=line.model_qty,
                unit=unit,
            )
        )
    all_match = bool(results) and all(item.outcome == "MATCH" for item in results)
    return SpecVolumeCompareResult(
        lines=tuple(results),
        all_match=all_match,
        checkpoint=CHECKPOINT,
        closes_rt001=False,
        closes_rt002=False,
        closes_rt003=False,
        claim_boundary=CLAIM_BOUNDARY,
    )


def spec_volume_honesty_snapshot() -> dict[str, object]:
    """Capabilities block: quantity triple ≠ estimate QTO."""

    return {
        "artifact_type": "spec_volume_compare",
        "requirement": "TR-67",
        "answers_clause": "2.1.3",
        "claim_level": "coverage_map_only",
        "checkpoint": CHECKPOINT,
        "estimate_qto": "not_in_scope",
        "customer_pack": "not_ingested",
        "ingest": "not_wired",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "SpecVolumeCompareResult",
    "SpecVolumeLine",
    "SpecVolumeLineResult",
    "compare_spec_volumes",
    "spec_volume_honesty_snapshot",
]
