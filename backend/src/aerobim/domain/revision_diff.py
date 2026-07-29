"""Revision diff (P1): compare findings between two package report revisions.

Verdict-neutral observability (competitive P1 «revision control»): given two
``ValidationReport``s of the same package at different revisions, report which findings
are newly reported, no-longer reported, or still reported, plus the finding-referenced
IFC element-GUID delta (appeared / disappeared elements).

ЧЕСТНО (после урока карты покрытия): ``no_longer_reported`` означает «было в старой,
нет в новой» — это НЕ утверждение «исправлено» (проверка могла просто не выполниться;
сверяйте с картой покрытия). Сравниваются ТОЛЬКО находки + элементы, на которые они
ссылаются, а не полный инвентарь IFC. Не читает и не выставляет ``summary.passed`` (ADR-001).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from aerobim.domain.models import ValidationIssue, ValidationReport


def _finding_key(issue: ValidationIssue) -> str:
    """Stable identity: prefer finding_id, else a deterministic composite."""
    if issue.finding_id:
        return f"fid:{issue.finding_id}"
    parts = (
        issue.rule_id or "",
        issue.category.value,
        issue.element_guid or "",
        issue.target_ref or "",
        issue.source_id or "",
    )
    return "key:" + "|".join(parts)


def _finding_keys(issues: Sequence[ValidationIssue]) -> set[str]:
    return {_finding_key(issue) for issue in issues}


def _element_guids(issues: Sequence[ValidationIssue]) -> set[str]:
    return {issue.element_guid for issue in issues if issue.element_guid}


@dataclass(frozen=True)
class RevisionDiff:
    """Finding + finding-referenced element delta between two report revisions."""

    old_report_id: str
    new_report_id: str
    old_revision: str | None
    new_revision: str | None
    newly_reported: tuple[str, ...]
    no_longer_reported: tuple[str, ...]
    still_reported: tuple[str, ...]
    elements_only_in_old: tuple[str, ...]
    elements_only_in_new: tuple[str, ...]

    def summary(self) -> dict[str, int]:
        return {
            "newly_reported": len(self.newly_reported),
            "no_longer_reported": len(self.no_longer_reported),
            "still_reported": len(self.still_reported),
            "elements_only_in_old": len(self.elements_only_in_old),
            "elements_only_in_new": len(self.elements_only_in_new),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "revision-diff",
            "note": (
                "finding delta between two report revisions; 'no_longer_reported' means "
                "present-in-old/absent-in-new and does NOT claim 'resolved' (check may not "
                "have re-run); verdict-neutral — does NOT set summary.passed (ADR-001)"
            ),
            "old_report_id": self.old_report_id,
            "new_report_id": self.new_report_id,
            "old_revision": self.old_revision,
            "new_revision": self.new_revision,
            "newly_reported": list(self.newly_reported),
            "no_longer_reported": list(self.no_longer_reported),
            "still_reported": list(self.still_reported),
            "elements_only_in_old": list(self.elements_only_in_old),
            "elements_only_in_new": list(self.elements_only_in_new),
            "summary": self.summary(),
        }


def compare_report_revisions(old: ValidationReport, new: ValidationReport) -> RevisionDiff:
    """Deterministically diff findings + referenced elements across two revisions.

    Verdict-neutral: reads only issues + identity/revision metadata, never
    ``summary.passed``. Keys are sorted for reproducibility.
    """
    old_keys = _finding_keys(old.issues)
    new_keys = _finding_keys(new.issues)
    old_elements = _element_guids(old.issues)
    new_elements = _element_guids(new.issues)
    return RevisionDiff(
        old_report_id=old.report_id,
        new_report_id=new.report_id,
        old_revision=old.revision,
        new_revision=new.revision,
        newly_reported=tuple(sorted(new_keys - old_keys)),
        no_longer_reported=tuple(sorted(old_keys - new_keys)),
        still_reported=tuple(sorted(new_keys & old_keys)),
        elements_only_in_old=tuple(sorted(old_elements - new_elements)),
        elements_only_in_new=tuple(sorted(new_elements - old_elements)),
    )


__all__ = [
    "RevisionDiff",
    "compare_report_revisions",
]
