"""Tests for reviewer priority profiles (TechLab)."""

from __future__ import annotations

import unittest

from aerobim.domain.models import (
    ConflictKind,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.review_priority import compute_issue_priority


class ReviewPriorityTests(unittest.TestCase):
    def test_default_cross_document_hard_conflict(self) -> None:
        issue = ValidationIssue(
            rule_id="XDOC-001",
            severity=Severity.ERROR,
            message="mismatch",
            category=FindingCategory.CROSS_DOCUMENT,
            conflict_kind=ConflictKind.HARD_CONFLICT,
        )
        self.assertEqual(compute_issue_priority(issue, profile="default"), 55)

    def test_unparsed_numeric_matches_hard_conflict_priority(self) -> None:
        issue = ValidationIssue(
            rule_id="XDOC-UNPARSED",
            severity=Severity.ERROR,
            message="unparsed",
            category=FindingCategory.CROSS_DOCUMENT,
            conflict_kind=ConflictKind.UNPARSED_NUMERIC,
        )
        self.assertEqual(compute_issue_priority(issue, profile="default"), 55)

    def test_pilot_boosts_fire_rule(self) -> None:
        issue = ValidationIssue(
            rule_id="REQ-FIRE-001",
            severity=Severity.ERROR,
            message="fire",
            category=FindingCategory.IFC_VALIDATION,
        )
        default_score = compute_issue_priority(issue, profile="default")
        pilot_score = compute_issue_priority(issue, profile="pilot")
        self.assertEqual(default_score, 30)
        self.assertEqual(pilot_score, 35)

    def test_pilot_boosts_cross_document(self) -> None:
        issue = ValidationIssue(
            rule_id="XDOC-002",
            severity=Severity.WARNING,
            message="cross",
            category=FindingCategory.CROSS_DOCUMENT,
        )
        default_score = compute_issue_priority(issue, profile="default")
        pilot_score = compute_issue_priority(issue, profile="pilot")
        self.assertGreater(pilot_score, default_score)


if __name__ == "__main__":
    unittest.main()
