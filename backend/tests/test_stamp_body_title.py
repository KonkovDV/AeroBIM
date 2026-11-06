"""The stamp name and the body title are two readings. Neither is the norm."""

from __future__ import annotations

import unittest

from aerobim.domain.models import DrawingAnnotation, FindingCategory, Severity, ValidationIssue
from aerobim.domain.review_priority import compute_issue_priority
from aerobim.domain.stamp_caption_above import (
    SHEET_BODY_TITLE_SOURCE,
    STAMP_BODY_TITLE_DISAGREE,
    STAMP_CAPTION_SOURCE,
    PlacedLine,
    disagreeing_stamp_and_body_titles,
    pair_captions_above_values,
    select_body_title,
    writes_summary_passed,
)


def _line(text: str, *, x: float, y: float, height: float, width: float = 80.0) -> PlacedLine:
    return PlacedLine(text=text, x=x, y=y, width=width, height=height)


class BodyTitleSelectionTests(unittest.TestCase):
    def test_the_tallest_letter_line_outside_the_block_is_the_title(self) -> None:
        chosen = select_body_title(
            (
                _line("Table", x=40, y=40, height=18),
                _line("note", x=40, y=80, height=8),
            ),
            page_width=1000,
            page_height=1000,
        )
        self.assertIsNotNone(chosen)
        assert chosen is not None
        self.assertEqual(chosen.text, "Table")

    def test_two_equally_tall_different_lines_yield_no_title(self) -> None:
        chosen = select_body_title(
            (
                _line("Table", x=40, y=40, height=18),
                _line("Shelf", x=200, y=40, height=18),
            ),
            page_width=1000,
            page_height=1000,
        )
        self.assertIsNone(chosen)

    def test_a_line_inside_the_title_block_is_not_the_body_title(self) -> None:
        chosen = select_body_title(
            (_line("StampName", x=900, y=960, height=22),),
            page_width=1000,
            page_height=1000,
        )
        self.assertIsNone(chosen)

    def test_a_measure_line_is_not_a_title(self) -> None:
        chosen = select_body_title(
            (_line("WALL-01 thickness 250 mm", x=40, y=40, height=18, width=160),),
            page_width=1000,
            page_height=1000,
        )
        self.assertIsNone(chosen)

    def test_a_paired_size_is_not_a_title(self) -> None:
        chosen = select_body_title(
            (_line("500x300", x=40, y=40, height=22),),
            page_width=1000,
            page_height=1000,
        )
        self.assertIsNone(chosen)

    def test_name_caption_pairs_with_the_cell_beneath(self) -> None:
        pairs = pair_captions_above_values(
            (
                _line("Наименование", x=40, y=40, height=10),
                _line("Shelf", x=40, y=52, height=12),
            )
        )
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].code, "name")
        self.assertEqual(pairs[0].value, "Shelf")


class StampBodyTitleDisagreeTests(unittest.TestCase):
    def test_different_readings_are_a_warning_without_a_required_name(self) -> None:
        issues = disagreeing_stamp_and_body_titles(
            (
                DrawingAnnotation(
                    annotation_id="stamp-1",
                    sheet_id="A-7",
                    target_ref="STAMP-NAME",
                    measure_name="name",
                    observed_value="Shelf",
                    source=STAMP_CAPTION_SOURCE,
                ),
                DrawingAnnotation(
                    annotation_id="body-1",
                    sheet_id="A-7",
                    target_ref="SHEET-TITLE",
                    measure_name="name",
                    observed_value="Table",
                    source=SHEET_BODY_TITLE_SOURCE,
                ),
            )
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, STAMP_BODY_TITLE_DISAGREE)
        self.assertIs(issues[0].severity, Severity.WARNING)
        self.assertIsNone(issues[0].expected_value)
        self.assertIn("Shelf", issues[0].message)
        self.assertIn("Table", issues[0].message)
        self.assertFalse(writes_summary_passed())
        drawing_error = ValidationIssue(
            rule_id="REQ-DRW-001",
            severity=Severity.ERROR,
            message="drawing",
            category=FindingCategory.DRAWING_VALIDATION,
        )
        self.assertLess(compute_issue_priority(issues[0]), compute_issue_priority(drawing_error))

    def test_the_same_name_is_quiet(self) -> None:
        issues = disagreeing_stamp_and_body_titles(
            (
                DrawingAnnotation(
                    annotation_id="stamp-1",
                    sheet_id="A-7",
                    target_ref="STAMP-NAME",
                    measure_name="name",
                    observed_value="Shelf",
                    source=STAMP_CAPTION_SOURCE,
                ),
                DrawingAnnotation(
                    annotation_id="body-1",
                    sheet_id="A-7",
                    target_ref="SHEET-TITLE",
                    measure_name="name",
                    observed_value="Shelf",
                    source=SHEET_BODY_TITLE_SOURCE,
                ),
            )
        )
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
