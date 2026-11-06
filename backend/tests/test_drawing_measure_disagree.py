"""Two sheets can print two numbers for one measure. Neither is the norm."""

from __future__ import annotations

import unittest

from aerobim.domain.drawing_measure_disagree import (
    DRAWING_MEASURE_DISAGREE,
    disagreeing_drawing_measures,
    writes_summary_passed,
)
from aerobim.domain.models import DrawingAnnotation, Severity
from aerobim.domain.review_priority import compute_issue_priority
from aerobim.domain.stamp_caption_above import STAMP_CAPTION_SOURCE


def _ann(
    target: str,
    measure: str,
    value: str,
    sheet: str,
    *,
    source: str = "raster-drawing-analyzer",
    unit: str = "шт",
) -> DrawingAnnotation:
    return DrawingAnnotation(
        annotation_id=f"{sheet}-{measure}-{value}",
        sheet_id=sheet,
        target_ref=target,
        measure_name=measure,
        observed_value=value,
        unit=unit,
        source=source,
    )


class DrawingMeasureDisagreeTests(unittest.TestCase):
    def test_two_counts_are_a_warning_without_a_required_value(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("LAMP-A", "count", "28", "PLAN"),
                _ann("LAMP-A", "count", "27", "SPEC"),
            )
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, DRAWING_MEASURE_DISAGREE)
        self.assertIs(issues[0].severity, Severity.WARNING)
        self.assertIsNone(issues[0].expected_value)
        self.assertIn("PLAN", issues[0].message)
        self.assertIn("SPEC", issues[0].message)
        self.assertFalse(writes_summary_passed())
        from aerobim.domain.models import FindingCategory, ValidationIssue

        drawing_error = ValidationIssue(
            rule_id="REQ-DRW-001",
            severity=Severity.ERROR,
            message="drawing",
            category=FindingCategory.DRAWING_VALIDATION,
        )
        self.assertLess(compute_issue_priority(issues[0]), compute_issue_priority(drawing_error))

    def test_trailing_zero_is_the_same_count(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("LAMP-A", "count", "28", "PLAN"),
                _ann("LAMP-A", "count", "28.0", "SPEC"),
            )
        )
        self.assertEqual(issues, [])

    def test_a_stamp_caption_is_not_a_measure(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("STAMP-SHEET", "sheet", "41", "A", source=STAMP_CAPTION_SOURCE, unit=""),
                _ann("STAMP-SHEET", "sheet", "42", "B", source=STAMP_CAPTION_SOURCE, unit=""),
            )
        )
        self.assertEqual(issues, [])

    def test_two_execution_tokens_are_a_warning_without_a_required_value(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("ITEM-A", "execution", "T", "PLAN", unit=""),
                _ann("ITEM-A", "execution", "F", "SPEC", unit=""),
            )
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, DRAWING_MEASURE_DISAGREE)
        self.assertIsNone(issues[0].expected_value)
        self.assertIn("T", issues[0].message)
        self.assertIn("F", issues[0].message)

    def test_the_same_execution_token_is_quiet(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("ITEM-A", "execution", "T", "PLAN", unit=""),
                _ann("ITEM-A", "execution", "T", "SPEC", unit=""),
            )
        )
        self.assertEqual(issues, [])

    def test_one_sheet_read_twice_is_quiet(self) -> None:
        issues = disagreeing_drawing_measures(
            (
                _ann("LAMP-A", "count", "28", "PLAN"),
                _ann("LAMP-A", "count", "27", "PLAN"),
            )
        )
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
