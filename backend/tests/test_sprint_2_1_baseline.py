"""Sprint 2.1 baseline CLI metrics schema / claim labeling."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_sprint_2_1_baseline import run_baseline

REPO = Path(__file__).resolve().parents[2]
PACK = REPO / "samples" / "benchmarks" / "sprint-2-1" / "baseline-package.json"


class Sprint21BaselineTests(unittest.TestCase):
    def test_baseline_metrics_schema(self) -> None:
        report = run_baseline(
            pack_path=PACK,
            iterations=1,
            warmup_iterations=0,
            run_analyze=False,
        )
        self.assertEqual(report["artifact_type"], "sprint_2_1_baseline")
        self.assertFalse(report["customer_evidence"])
        self.assertEqual(report["claim_level"], "engineering_baseline_only")
        self.assertIn("metrics", report)
        self.assertEqual(report["pdf_generation"], "PDF_GENERATION_BLOCKED")
        self.assertIn("RT-001", report["warning"])

    def test_tp_fp_fn_accounting(self) -> None:
        report = run_baseline(
            pack_path=PACK,
            iterations=1,
            warmup_iterations=0,
            run_analyze=False,
        )
        metrics = report["metrics"]
        # Lightweight CLI intentionally leaves TP/FP/FN null until mutation+analyze.
        self.assertIsNone(metrics["tp"])
        self.assertIsNone(metrics["fp"])
        self.assertIsNone(metrics["fn"])
        self.assertGreaterEqual(metrics["declared_finding_cases"], 1)

    def test_timing_artifact(self) -> None:
        report = run_baseline(
            pack_path=PACK,
            iterations=2,
            warmup_iterations=0,
            run_analyze=False,
        )
        self.assertEqual(len(report["metrics"]["time_total_samples_s"]), 2)
        self.assertGreater(report["metrics"]["time_total_mean_s"], 0)

    def test_customer_claim_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            payload = json.loads(PACK.read_text(encoding="utf-8"))
            payload["customer_evidence"] = True
            bad.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                run_baseline(
                    pack_path=bad,
                    iterations=1,
                    warmup_iterations=0,
                    run_analyze=False,
                )

    def test_fixture_claim_label(self) -> None:
        report = run_baseline(
            pack_path=PACK,
            iterations=1,
            warmup_iterations=0,
            run_analyze=False,
        )
        self.assertIn("engineering_baseline", report["claim_level"])
        self.assertNotIn("product_accuracy", report["claim_level"])


if __name__ == "__main__":
    unittest.main()
