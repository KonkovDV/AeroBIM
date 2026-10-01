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

    def test_corridor_and_mop_names_are_hints_not_verdicts(self) -> None:
        from aerobim.domain.space_efficiency_advisory import layout_hint_for_space

        corridor = SpaceInventoryRow(guid="c1", name="Коридор 1 этаж")
        mop = SpaceInventoryRow(guid="m1", long_name="МОП секции 2")
        room = SpaceInventoryRow(guid="r1", name="Спальня")
        self.assertEqual(layout_hint_for_space(corridor), "corridor")
        self.assertEqual(layout_hint_for_space(mop), "common_area")
        self.assertEqual(layout_hint_for_space(room), "other")
        issues = build_space_efficiency_candidates((corridor, mop, room))
        package = issues[0].message
        self.assertIn("corridor=1", package)
        self.assertIn("common_area=1", package)
        self.assertIn("layout_hint=corridor", issues[1].message)
        self.assertNotIn("inefficient by", package.lower())

    def test_missing_qto_is_not_tep_does_not(self) -> None:
        spaces = (SpaceInventoryRow(guid="g1", name="Room"),)
        issues = build_space_efficiency_candidates(spaces)
        self.assertIn("not a TEP Does-not", issues[0].message)
        self.assertIn("never sets summary.passed", issues[0].message)


if __name__ == "__main__":
    unittest.main()
