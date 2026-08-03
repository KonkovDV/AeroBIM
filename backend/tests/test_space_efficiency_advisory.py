"""Space-efficiency advisory — verdict-neutral fixture tests (TZ row 19)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import Severity
from aerobim.domain.space_efficiency_advisory import (
    SpaceInventoryRow,
    build_space_efficiency_candidates,
)


class SpaceEfficiencyAdvisoryTests(unittest.TestCase):
    def test_empty_inventory_emits_nothing(self) -> None:
        self.assertEqual(build_space_efficiency_candidates(()), ())

    def test_candidates_are_info_advisory_ai_generated(self) -> None:
        spaces = (
            SpaceInventoryRow(guid="g1", name="Bedroom", net_floor_area=12.5),
            SpaceInventoryRow(guid="g2", name="Toilet", net_floor_area=3.0),
        )
        issues = build_space_efficiency_candidates(spaces, layout_note="open plan center")
        self.assertGreaterEqual(len(issues), 1)
        for issue in issues:
            self.assertEqual(issue.severity, Severity.INFO)
            self.assertEqual(issue.origin, "advisory")
            self.assertIsNotNone(issue.remark)
            assert issue.remark is not None
            self.assertTrue(issue.remark.ai_generated)
            self.assertTrue(issue.remark.expert_confirmation_required)
            self.assertNotIn("inefficient by", issue.message.lower())
            self.assertNotIn("efficiency score", issue.message.lower())
            self.assertIn("no efficiency threshold", issue.message.lower())

    def test_no_numeric_efficiency_verdict_in_body(self) -> None:
        spaces = (SpaceInventoryRow(guid="g1", name="Hall", net_floor_area=40.0),)
        issues = build_space_efficiency_candidates(spaces)
        joined = " ".join(i.message for i in issues)
        # Forbidden product claims — inventory only.
        for banned in ("% efficient", "fails efficiency", "underutilized by", "score="):
            self.assertNotIn(banned, joined.lower())

    def test_layout_note_appended_when_provided(self) -> None:
        spaces = (SpaceInventoryRow(guid="g1", name="A"),)
        issues = build_space_efficiency_candidates(spaces, layout_note="corridor dominates")
        self.assertIn("corridor dominates", issues[0].message)


if __name__ == "__main__":
    unittest.main()
