"""Finding provenance helpers — every persisted issue must be bindable to a source."""

from __future__ import annotations

from uuid import uuid4

from aerobim.domain.models import ValidationIssue


def ensure_finding_provenance(
    issue: ValidationIssue,
    *,
    tenant_id: str | None = None,
    project_id: str | None = None,
    revision: str | None = None,
) -> ValidationIssue:
    """Stamp stable finding_id and fill missing source/evidence pointers."""

    finding_id = issue.finding_id or uuid4().hex
    source_id = issue.source_id or "unspecified"
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
    return ValidationIssue(
        **{
            **issue.__dict__,
            "finding_id": finding_id,
            "source_id": source_id,
            "evidence_refs": evidence_refs,
            "tenant_id": issue.tenant_id or tenant_id,
            "project_id": issue.project_id or project_id,
        }
    )


def assert_finding_persistable(issue: ValidationIssue) -> None:
    """Raise if a finding cannot be audited (rule/source/evidence missing)."""

    if not (issue.rule_id or "").strip():
        raise ValueError("ValidationIssue.rule_id is required for persistence")
    if not (issue.finding_id or "").strip():
        raise ValueError("ValidationIssue.finding_id is required for persistence")
    if not (issue.source_id or "").strip():
        raise ValueError("ValidationIssue.source_id is required for persistence")
    if not issue.evidence_refs:
        raise ValueError("ValidationIssue.evidence_refs is required for persistence")


__all__ = ["assert_finding_persistable", "ensure_finding_provenance"]
