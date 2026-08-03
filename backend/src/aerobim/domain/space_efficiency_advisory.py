"""Candidate space-efficiency observations — advisory only, no numeric thresholds.

TZ row 19: surface IFC space inventory (+ optional layout note from a PII-gated
plan crop) as INFO findings with ``origin=advisory`` and expert confirmation.
Never sets severity ERROR/WARNING and never participates in ``summary.passed``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import (
    FindingCategory,
    GeneratedRemark,
    Severity,
    ValidationIssue,
)


@dataclass(frozen=True)
class SpaceInventoryRow:
    """Minimal IFC space row for advisory provenance (no efficiency math)."""

    guid: str
    name: str | None = None
    long_name: str | None = None
    net_floor_area: float | None = None
    predefined_type: str | None = None


_RULE_ID = "AEROBIM-SPACE-EFFICIENCY-CANDIDATE"
_CLAIM = (
    "Advisory layout observation only; no efficiency threshold; "
    "ai_generated requires expert confirmation; never sets summary.passed"
)


def build_space_efficiency_candidates(
    spaces: Sequence[SpaceInventoryRow],
    *,
    layout_note: str | None = None,
    source_id: str = "space-efficiency-advisory",
    max_candidates: int = 8,
) -> tuple[ValidationIssue, ...]:
    """Emit candidate observations from space inventory (+ optional VLM note).

    No numeric cutoffs (occupancy %, underuse ratios, etc.). The observation is
    a human-readable inventory summary that an expert must confirm or dismiss.
    """

    if not spaces:
        return ()

    cap = max(0, int(max_candidates))
    if cap == 0:
        return ()

    total = len(spaces)
    with_area = sum(1 for row in spaces if row.net_floor_area is not None)
    area_sum = sum(row.net_floor_area or 0.0 for row in spaces if row.net_floor_area is not None)
    area_fragment = (
        f"Spaces with NetFloorArea: {with_area}/{total}; sum≈{area_sum:.2f}."
        if with_area
        else f"Spaces without NetFloorArea quantities: {total}."
    )
    note_fragment = ""
    if layout_note and layout_note.strip():
        note_fragment = f" Layout note (PII-gated crop): {layout_note.strip()[:400]}"

    issues: list[ValidationIssue] = []
    # One package-level candidate, then per-space samples (capped).
    package_body = (
        f"Candidate space-efficiency observation for expert review. "
        f"{area_fragment}{_CLAIM}.{note_fragment}"
    )
    issues.append(
        ValidationIssue(
            rule_id=_RULE_ID,
            severity=Severity.INFO,
            message=package_body,
            ifc_entity="IfcSpace",
            category=FindingCategory.SPATIAL,
            finding_id=f"{_RULE_ID}:package",
            evidence_refs=("ifc:IfcSpace", "advisory:space-efficiency"),
            source_id=source_id,
            origin="advisory",
            confidence=0.0,
            remark=GeneratedRemark(
                title="Space-efficiency candidate (advisory)",
                body=package_body,
                ai_generated=True,
                expert_confirmation_required=True,
            ),
        )
    )

    for index, row in enumerate(spaces[: max(0, cap - 1)]):
        label = row.long_name or row.name or row.guid
        area_txt = (
            f"NetFloorArea={row.net_floor_area:.2f}"
            if row.net_floor_area is not None
            else "NetFloorArea=unknown"
        )
        type_txt = row.predefined_type or "untyped"
        body = (
            f"Candidate observation for space '{label}' ({type_txt}; {area_txt}). "
            f"No automated efficiency verdict. {_CLAIM}."
        )
        issues.append(
            ValidationIssue(
                rule_id=_RULE_ID,
                severity=Severity.INFO,
                message=body,
                ifc_entity="IfcSpace",
                category=FindingCategory.SPATIAL,
                element_guid=row.guid,
                target_ref=label,
                finding_id=f"{_RULE_ID}:{row.guid}",
                evidence_refs=(f"ifc:guid:{row.guid}", "advisory:space-efficiency"),
                source_id=source_id,
                origin="advisory",
                confidence=0.0,
                remark=GeneratedRemark(
                    title=f"Space candidate: {label}",
                    body=body,
                    ai_generated=True,
                    expert_confirmation_required=True,
                ),
            )
        )
        _ = index  # keep enumerate for stable ordering only

    return tuple(issues)


__all__ = ["SpaceInventoryRow", "build_space_efficiency_candidates"]
