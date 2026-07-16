"""ISO 19650-lite CDE status mapping for report metadata."""

from __future__ import annotations

from typing import Any

from aerobim.domain.models import DocStatus, ValidationReport

# Dual labels during ISO 19650 2026 terminology transition (EIR→IPR / CDE states).
_DOC_STATUS_LABELS: dict[str, dict[str, str]] = {
    "WIP": {
        "cde_state": "Work in Progress",
        "iso19650_container_state": "WorkInProgress",
        "description": "Authoring / private development; not yet shared for coordination",
    },
    "Shared": {
        "cde_state": "Shared",
        "iso19650_container_state": "Shared",
        "description": "Issued for coordination / review within the project team",
    },
    "Published": {
        "cde_state": "Published",
        "iso19650_container_state": "Published",
        "description": "Authorized information for use outside the authoring team",
    },
    "Archived": {
        "cde_state": "Archived",
        "iso19650_container_state": "Archived",
        "description": "Superseded or retained for record; not current for delivery",
    },
}


def enrich_iso19650_metadata(report: ValidationReport) -> dict[str, Any]:
    """Return machine-readable ISO 19650-lite container metadata for API clients."""
    status: DocStatus | None = report.doc_status
    status_key = str(status) if status is not None else None
    labels = _DOC_STATUS_LABELS.get(status_key or "", {})
    return {
        "information_container_id": report.information_container_id,
        "revision": report.revision,
        "stage": report.stage,
        "doc_status": status_key,
        "cde_state": labels.get("cde_state"),
        "iso19650_container_state": labels.get("iso19650_container_state"),
        "description": labels.get("description"),
        "acceptance_criteria_engine": "aerobim",
        "note": (
            "Decision-support evidence for CDE quality gates; "
            "not an organisational ISO 19650 certification claim"
        ),
    }
