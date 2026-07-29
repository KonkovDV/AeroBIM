"""P1 evidence: synthetic drawing-contour assessment routing + reproducibility.

Verifies the demo sheet exercises AUTO_READ + EXPERT_REVIEW, the anti-bad-scan
invariant (unreadable region is not classified), self-declares synthetic, is
verdict-neutral, and is reproducible vs the committed artifact.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.export_drawing_contour import synthetic_scenario

_ARTIFACT = (
    Path(__file__).resolve().parents[2] / "audit" / "evidence" / "drawing-contour-2026-07-29.json"
)


class ExportDrawingContourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = synthetic_scenario()

    def test_routing_has_both_actions(self) -> None:
        actions = self.report["summary"]["actions"]
        self.assertGreater(actions["auto_read"], 0)
        self.assertGreater(actions["expert_review"], 0)

    def test_unreadable_region_is_not_classified(self) -> None:
        # Anti-bad-scan: the unreadable scan (with valid-looking text) must not be typed.
        region = next(r for r in self.report["regions"] if r["label"] == "unreadable-scan")
        self.assertEqual(region["action"], "expert_review")
        self.assertEqual(region["quality"], "unreadable")
        self.assertIsNone(region["region_type"])

    def test_readable_stamp_is_auto_read(self) -> None:
        region = next(r for r in self.report["regions"] if r["label"] == "titleblock")
        self.assertEqual(region["action"], "auto_read")
        self.assertEqual(region["region_type"], "stamp")

    def test_self_declared_synthetic_and_verdict_neutral(self) -> None:
        self.assertEqual(self.report["corpus"], "synthetic")
        self.assertIn("no customer data", self.report["disclaimer"])
        self.assertIn("not product accuracy", self.report["disclaimer"])
        self.assertNotIn('"passed"', json.dumps(self.report))

    def test_reproducible_vs_committed_artifact(self) -> None:
        self.assertTrue(_ARTIFACT.exists(), "drawing-contour evidence artifact missing")
        # Regenerate on intentional change: python -m aerobim.tools.export_drawing_contour
        committed = json.loads(_ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(self.report, committed)


if __name__ == "__main__":
    unittest.main()
