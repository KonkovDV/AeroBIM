"""A cited detail with no sheet title is a warning, not a missing-norm claim."""

from __future__ import annotations

import unittest

from aerobim.domain.detail_callout import (
    DETAIL_CALLOUT_MISSING,
    DETAIL_CALLOUT_SOURCE,
    DETAIL_TITLE_SOURCE,
    detail_callout_id,
    detail_title_id,
    missing_detail_callouts,
    writes_summary_passed,
)
from aerobim.domain.models import DrawingAnnotation, FindingCategory, Severity, ValidationIssue
from aerobim.domain.review_priority import compute_issue_priority


def _detail(source: str, detail_id: str, sheet: str) -> DrawingAnnotation:
    return DrawingAnnotation(
        annotation_id=f"{sheet}-{source}-{detail_id}",
        sheet_id=sheet,
        target_ref=f"DETAIL-{detail_id}",
        measure_name="detail",
        observed_value=detail_id,
        source=source,
    )


class DetailCalloutTests(unittest.TestCase):
    def test_a_citation_without_a_title_is_a_warning(self) -> None:
        issues = missing_detail_callouts((_detail(DETAIL_CALLOUT_SOURCE, "1", "A-101"),))
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, DETAIL_CALLOUT_MISSING)
        self.assertIs(issues[0].severity, Severity.WARNING)
        self.assertIsNone(issues[0].expected_value)
        self.assertIn("A-101", issues[0].message)
        self.assertFalse(writes_summary_passed())
        drawing_error = ValidationIssue(
            rule_id="REQ-DRW-001",
            severity=Severity.ERROR,
            message="drawing",
            category=FindingCategory.DRAWING_VALIDATION,
        )
        self.assertLess(compute_issue_priority(issues[0]), compute_issue_priority(drawing_error))

    def test_a_title_on_another_sheet_keeps_the_citation_quiet(self) -> None:
        issues = missing_detail_callouts(
            (
                _detail(DETAIL_CALLOUT_SOURCE, "01", "A-101"),
                _detail(DETAIL_TITLE_SOURCE, "1", "A-200"),
            )
        )
        self.assertEqual(issues, [])

    def test_phrases(self) -> None:
        self.assertEqual(detail_callout_id("см. узел 1"), "1")
        self.assertEqual(detail_callout_id("see detail 12"), "12")
        self.assertEqual(detail_title_id("Узел 01"), "1")
        self.assertEqual(detail_title_id("Detail 3"), "3")
        self.assertIsNone(detail_title_id("см. узел 1"))
        self.assertIsNone(detail_callout_id("Узел 1"))
        self.assertIsNone(detail_title_id("Узел 1 на листе"))


if __name__ == "__main__":
    unittest.main()
