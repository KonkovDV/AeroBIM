"""Sprint 2 synthetic ground-truth inventory contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[2]


class Sprint2SyntheticGtTests(unittest.TestCase):
    def test_ground_truth_covers_six_tz_classes(self) -> None:
        path = REPO / "samples" / "benchmarks" / "sprint2-synthetic-ground-truth.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data.get("claim_level"), "synthetic_only")
        self.assertIs(data.get("closes_rt001"), False)
        classes = data.get("tz_error_classes") or []
        self.assertEqual(len(classes), 6)
        planted = data.get("planted_detectable") or []
        self.assertGreaterEqual(len(planted), 5)
        for row in planted:
            self.assertIn("match_key", row)
            self.assertIn("defect_id", row)

    def test_metrics_method_doc_exists(self) -> None:
        path = REPO / "docs" / "pilot" / "SPRINT2_DETECTION_METRICS_METHOD_2026_08.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("Wilson", text)
        self.assertIn("Match rule", text)
        self.assertIn("synthetic", text.lower())


if __name__ == "__main__":
    unittest.main()
