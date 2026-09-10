"""Requirement-row ↔ AeroBIM check-family crosswalk. Not TP/FP. No auto-match."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO
from aerobim.domain.customer_review_book import eligible_for_fn

CLAIM_BOUNDARY: Final = (
    "Human crosswalk of checklist requirement rows to check families. "
    "Agreement is requirement-status agreement, not precision. "
    "One adjudicator keeps publishable false. Checkpoint GO; customer_go false."
)

MachineVerifiability = Literal[
    "machine_full",
    "machine_partial",
    "needs_document",
    "needs_human",
    "out_of_scope",
]


def _as_row(item: Mapping[str, Any]) -> dict[str, Any]:
    assigned_by = str(item.get("assigned_by") or "").strip().casefold()
    verifiability = str(item.get("machine_verifiability") or "")
    coverage = str(item.get("coverage_status") or "")
    return {
        "row_id": item.get("row_id"),
        "machine_verifiability": verifiability,
        "assigned_by": assigned_by,
        "coverage_status": coverage,
        "check_family": item.get("check_family") or "",
        "matched_finding_ids": list(item.get("matched_finding_ids") or []),
        "stage_mismatch": bool(item.get("stage_mismatch")),
        "llm_assigned": assigned_by == "llm",
    }


def build_requirement_crosswalk(
    rows: Sequence[Mapping[str, Any]],
    *,
    adjudicators: int = 1,
) -> dict[str, Any]:
    labelled = [_as_row(item) for item in rows]
    for item in labelled:
        item["matched_finding_ids"] = []  # never auto-fill
    usable = [item for item in labelled if not item["llm_assigned"]]
    total = len(usable)
    machine = [
        item
        for item in usable
        if item["machine_verifiability"] in {"machine_full", "machine_partial"}
    ]
    closed = [item for item in machine if item["coverage_status"] == "checked"]
    agreement_den = [
        item
        for item in usable
        if item["machine_verifiability"] == "machine_full" and item["coverage_status"] == "checked"
    ]
    fn_rows = [
        item
        for item in usable
        if eligible_for_fn(
            coverage_status=str(item.get("coverage_status") or ""),
            stage_mismatch=bool(item.get("stage_mismatch")),
        )
        and item["machine_verifiability"] in {"machine_full", "machine_partial"}
        and item["coverage_status"] == "checked"
        and not item.get("matched_finding_ids")
    ]
    return {
        "schema_version": "1.0.0",
        "artifact_type": "requirement_crosswalk",
        "claim_boundary": CLAIM_BOUNDARY,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "is_accuracy": False,
        "publishable": False,
        "adjudicators": adjudicators,
        "totals": {
            "requirement_rows": total,
            "machine_verifiable": len(machine),
            "closed_by_run": len(closed),
        },
        "agreement": {
            "denominator": len(agreement_den),
            "label": "согласие по требованию, не точность",
        },
        "fn_eligible": len(fn_rows),
        "rows": labelled,
        "auto_match": False,
    }
