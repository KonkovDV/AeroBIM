"""IFC-Bench smoke: countable probes + claim_level honesty."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class IfcBenchSmokeTests(unittest.TestCase):
    def test_parse_expected_number(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import _parse_expected_number

        self.assertEqual(_parse_expected_number("There are 10 interior doors."), 10.0)
        self.assertEqual(_parse_expected_number("There are 4 bedrooms in the building."), 4.0)
        self.assertEqual(
            _parse_expected_number(
                "The model specifies 14 light fixtures: 8 pendant and 6 sconce lights."
            ),
            14.0,
        )
        self.assertIsNone(
            _parse_expected_number("I cannot calculate the number of window on the north facade.")
        )

    def test_evaluate_requires_dataset(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                evaluate_dataset(Path(tmp))

    def test_live_dataset_smoke_when_present(self) -> None:
        from aerobim.tools.run_ifc_bench_smoke import evaluate_dataset, repo_root

        root = repo_root() / ".local" / "ifc-bench"
        if not (root / "questions" / "ifc-bench-v1.csv").is_file():
            self.skipTest("IFC-Bench checkout not present under .local/ifc-bench")
        payload = evaluate_dataset(root)
        self.assertEqual(payload["claim_level"], "open_bench_only")
        self.assertFalse(payload["closes_rt001"])
        self.assertGreaterEqual(payload["summary"]["scored"], 5)
        self.assertEqual(payload["summary"]["mismatched"], 0)
        self.assertEqual(payload["summary"]["exact_match_rate_on_scored"], 1.0)
        # Round-trip JSON for evidence shape.
        raw = json.dumps(payload)
        self.assertIn("open_bench_only", raw)


if __name__ == "__main__":
    unittest.main()
