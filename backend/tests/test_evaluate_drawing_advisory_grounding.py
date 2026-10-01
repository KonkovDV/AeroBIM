"""Advisory drawing-grounding harness — fidelity on the synthetic fixture + honesty.

The harness measures the DETERMINISTIC advisory pipeline on canned reads; it must
detect mismatches (not vacuously pass) and must label itself as fixture-only, not
model/product accuracy. It can never change a verdict (advisory contour).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.evaluate_drawing_advisory_grounding import (
    evaluate_drawing_advisory_grounding,
    threshold_failures,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "samples"
    / "benchmarks"
    / "drawing-advisory"
    / "cases-synthetic.json"
)


class DrawingAdvisoryGroundingHarnessTests(unittest.TestCase):
    def test_committed_fixture_full_fidelity(self) -> None:
        report = evaluate_drawing_advisory_grounding(_FIXTURE)
        self.assertEqual(report["grounding_fidelity"], 1.0)
        self.assertEqual(report["matched_cases"], report["total_cases"])
        self.assertGreaterEqual(report["total_cases"], 8)
        self.assertTrue(all(case["matched"] for case in report["per_case"]))  # type: ignore[index]
        self.assertEqual(threshold_failures(report, min_fidelity=1.0), [])

    def test_honesty_framing_is_explicit(self) -> None:
        report = evaluate_drawing_advisory_grounding(_FIXTURE)
        self.assertEqual(report["dataset_status"], "synthetic")
        self.assertEqual(report["artifact_type"], "aerobim_drawing_advisory_grounding_evaluation")
        self.assertIn("NOT model or product accuracy", str(report["warning"]))
        self.assertIn("AeroBIM product accuracy", report["does_not_measure"])  # type: ignore[operator]

    def test_harness_detects_a_mismatch(self) -> None:
        # A deliberately wrong expectation must FAIL (guards against a vacuous pass):
        # the uncalibrated read yields hitl_count=1, but expected says 0.
        payload = {
            "schema_version": "1.0.0",
            "dataset_id": "mismatch",
            "dataset_status": "synthetic",
            "cases": [
                {
                    "case_id": "wrong",
                    "vlm_response": {
                        "readable": True,
                        "observations": [
                            {
                                "kind": "dimension",
                                "raw_value": "200",
                                "bbox_rel": [0.1, 0.1, 0.3, 0.3],
                                "confidence": 0.9,
                            }
                        ],
                    },
                    "expected": {"hitl_count": 0},
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = evaluate_drawing_advisory_grounding(path)
        self.assertEqual(report["grounding_fidelity"], 0.0)
        self.assertFalse(report["per_case"][0]["matched"])  # type: ignore[index]
        self.assertTrue(threshold_failures(report, min_fidelity=1.0))

    def test_rejects_wrong_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps({"schema_version": "9.9.9", "cases": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                evaluate_drawing_advisory_grounding(path)


if __name__ == "__main__":
    unittest.main()
