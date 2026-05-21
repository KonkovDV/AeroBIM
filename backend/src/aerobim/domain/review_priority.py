"""Reviewer priority scoring for assistive QA workflows (incl. Samolet TechLab)."""

from __future__ import annotations

from aerobim.domain.models import ConflictKind, FindingCategory, ValidationIssue

_VALID_PROFILES = frozenset({"default", "samolet"})


def compute_issue_priority(issue: ValidationIssue, profile: str = "default") -> int:
    """Score issues for export sort order and BCF triage (higher = more urgent)."""
    normalized = profile.strip().lower() if profile else "default"
    if normalized not in _VALID_PROFILES:
        normalized = "default"

    sev_score = {"error": 30, "warning": 20, "info": 10}.get(issue.severity.value, 0)
    cat_score = {
        FindingCategory.CROSS_DOCUMENT: 15,
        FindingCategory.IDS_VALIDATION: 10,
        FindingCategory.DRAWING_VALIDATION: 5,
        FindingCategory.IFC_VALIDATION: 0,
    }.get(issue.category, 0)
    conflict_score = 10 if issue.conflict_kind == ConflictKind.HARD_CONFLICT else 0
    score = sev_score + cat_score + conflict_score

    if normalized == "samolet":
        score += _samolet_profile_boost(issue)

    return score


def _samolet_profile_boost(issue: ValidationIssue) -> int:
    """Boost fire-safety and cross-document findings per Samolet task emphasis."""
    boost = 0
    rule_id = (issue.rule_id or "").upper()

    if issue.category == FindingCategory.CROSS_DOCUMENT:
        boost += 5
    if rule_id.startswith("REQ-FIRE"):
        boost += 5
    elif rule_id.startswith("REQ-STRUCT"):
        boost += 3
    elif rule_id.startswith("REQ-MEP"):
        boost += 2

    return boost
