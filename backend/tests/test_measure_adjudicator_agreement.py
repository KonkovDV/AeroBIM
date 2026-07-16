"""Tests for Cohen's κ adjudication agreement tool."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.measure_adjudicator_agreement import cohen_kappa, measure_adjudication_csv


class AdjudicatorAgreementTests(unittest.TestCase):
    def test_cohen_kappa_perfect_agreement(self) -> None:
        self.assertEqual(cohen_kappa(["TP", "FP", "FN"], ["TP", "FP", "FN"]), 1.0)

    def test_cohen_kappa_chance_only_is_zero(self) -> None:
        # Classic balanced mismatch → κ ≈ 0
        kappa = cohen_kappa(["TP", "TP", "FP", "FP"], ["TP", "FP", "TP", "FP"])
        self.assertAlmostEqual(kappa, 0.0, places=6)

    def test_template_csv_reports_matrix_and_kappa(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        csv_path = (
            repo / "samples" / "benchmarks" / "detection-precision" / "adjudication-template.csv"
        )
        self.assertTrue(csv_path.exists())
        payload = measure_adjudication_csv(csv_path)
        self.assertEqual(payload["artifact_type"], "adjudicator_agreement")
        self.assertEqual(payload["paired_items"], 4)
        self.assertIn("confusion_matrix", payload)
        self.assertLess(float(payload["cohens_kappa"]), 1.0)  # one TP/FP disagreement

    def test_requires_two_adjudicators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.csv"
            path.write_text(
                "finding_id,adjudicator_id,verdict\nf1,engineer-a,TP\nf2,engineer-a,FP\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                measure_adjudication_csv(path)


if __name__ == "__main__":
    unittest.main()
