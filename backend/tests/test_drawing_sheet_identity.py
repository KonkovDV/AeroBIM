"""Drawing sheet identity guard tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.ingestion import (
    detect_missing_drawing_sheet_identity,
    drawing_sheet_identity,
)
from aerobim.domain.models import DrawingSource, Severity


class DrawingSheetIdentityTests(unittest.TestCase):
    def test_drawing_sheet_identity_prefers_sheet_id(self) -> None:
        source = DrawingSource(sheet_id="A-101", path=Path("ignored.txt"))
        self.assertEqual(drawing_sheet_identity(source), "A-101")

    def test_detect_missing_identity_warns_on_anonymous_drawing(self) -> None:
        issues = detect_missing_drawing_sheet_identity([DrawingSource(text="annotation only")])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "AEROBIM-SHEET-IDENTITY")
        self.assertEqual(issues[0].severity, Severity.WARNING)

    def test_path_stem_counts_as_identity(self) -> None:
        issues = detect_missing_drawing_sheet_identity(
            [DrawingSource(path=Path("samples/drawings/plan-a.txt"))]
        )
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
