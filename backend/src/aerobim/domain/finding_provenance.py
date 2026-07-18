"""Finding provenance helpers — every persisted issue must be bindable to a source.

finding_id is deterministic (content hash), never random uuid4, so the same
deterministic finding reproduces across runs and advisory ON/OFF.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from aerobim.domain.models import ValidationIssue

FindingOrigin = Literal["deterministic", "advisory"]

_WEAK_SOURCE_IDS = frozenset({"", "unspecified", "none", "null", "unknown"})


def compute_stable_finding_id(issue: ValidationIssue) -> str:
    """SHA-256 hex of structural finding identity (32 chars)."""

    category = issue.category.value if issue.category is not None else ""
    parts = (
        issue.rule_id or "",
        issue.source_id or "",
        category,
        issue.element_guid or "",
        issue.target_ref or "",
        issue.property_set or "",
        issue.property_name or "",
        issue.expected_value or "",
        issue.observed_value or "",
        issue.conflict_kind.value if issue.conflict_kind is not None else "",
    )
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return digest[:32]


def ensure_finding_provenance(
    issue: ValidationIssue,
    *,
    tenant_id: str | None = None,
    project_id: str | None = None,
    revision: str | None = None,
    origin: FindingOrigin | None = None,
) -> ValidationIssue:
    """Stamp stable finding_id and fill missing source/evidence pointers."""

    source_id = (issue.source_id or "").strip()
    if source_id.casefold() in _WEAK_SOURCE_IDS:
        source_id = f"auto:{issue.category.value}:{issue.rule_id}"

    finding_id = (issue.finding_id or "").strip() or compute_stable_finding_id(
        ValidationIssue(
            **{
                **issue.__dict__,
                "source_id": source_id,
            }
        )
    )

    evidence_refs = issue.evidence_refs
    if not evidence_refs:
        pointer = source_id
        if revision:
            pointer = f"{pointer}@{revision}"
        if issue.element_guid:
            pointer = f"{pointer}#ifc:{issue.element_guid}"
        elif issue.problem_zone and issue.problem_zone.sheet_id:
            pointer = f"{pointer}#sheet:{issue.problem_zone.sheet_id}"
        evidence_refs = (pointer,)

    resolved_origin = origin or issue.origin or "deterministic"

    return ValidationIssue(
        **{
            **issue.__dict__,
            "finding_id": finding_id,
            "source_id": source_id,
            "evidence_refs": evidence_refs,
            "tenant_id": issue.tenant_id or tenant_id,
            "project_id": issue.project_id or project_id,
            "origin": resolved_origin,
        }
    )


def assert_finding_persistable(issue: ValidationIssue) -> None:
    """Raise if a finding cannot be audited (rule/source/evidence missing)."""

    if not (issue.rule_id or "").strip():
        raise ValueError("ValidationIssue.rule_id is required for persistence")
    if not (issue.finding_id or "").strip():
        raise ValueError("ValidationIssue.finding_id is required for persistence")
    source_id = (issue.source_id or "").strip()
    if not source_id or source_id.casefold() in _WEAK_SOURCE_IDS:
        raise ValueError("ValidationIssue.source_id must be a concrete non-placeholder id")
    if not issue.evidence_refs:
        raise ValueError("ValidationIssue.evidence_refs is required for persistence")


def is_finding_publishable(issue: ValidationIssue) -> bool:
    """True when finding_id, concrete source_id, and evidence_refs are present."""

    try:
        assert_finding_persistable(issue)
    except ValueError:
        return False
    return True


__all__ = [
    "FindingOrigin",
    "assert_finding_persistable",
    "compute_stable_finding_id",
    "ensure_finding_provenance",
    "is_finding_publishable",
]
