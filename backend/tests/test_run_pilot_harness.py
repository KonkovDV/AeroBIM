"""One-command pilot harness + ranking labels template (self-side plan P1/P3).

Closes Checkpoint #2 DoD items without customer data: stream 4 ("harness
одной командой") and the ranking-labels expert template. Pure orchestration
tests — statistical semantics are covered by the underlying evaluators'
suites. Claim boundary: synthetic/draft runs are never publishable (RT-001).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.evaluate_ranking_quality import evaluate_ranking_quality
from aerobim.tools.run_pilot_harness import main, run_pilot_harness

_REPO = Path(__file__).resolve().parents[2]
_DP = _REPO / "samples" / "benchmarks" / "detection-precision"


class RunPilotHarnessTests(unittest.TestCase):
    def test_one_command_produces_combined_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            combined = run_pilot_harness(
                labels_path=_DP / "labels-synthetic.json",
                detections_path=_DP / "detections-synthetic.json",
                adjudication_csv=_DP / "adjudication-template.csv",
                ranking_labels_path=_DP / "ranking-labels-template.json",
                output_dir=output,
            )
            # One command → precision/recall/F1 + κ/α + nDCG (DoD stream 4).
            self.assertEqual(combined["artifact_type"], "pilot_harness_report")
            self.assertIn("precision", combined["precision"]["micro"])
            self.assertIn("recall", combined["precision"]["micro"])
            self.assertIn("f1", combined["precision"]["micro"])
            self.assertIn("false_positive_burden", combined["precision"]["micro"])
            self.assertIsNotNone(combined["agreement"])
            self.assertIn("ndcg_full", combined["ranking"]["summary"])
            # Synthetic corpus can never be publishable product accuracy.
            self.assertFalse(combined["publishable"])
            for name in (
                "agreement.json",
                "precision-report.json",
                "ranking-report.json",
                "pilot-harness-report.json",
            ):
                self.assertTrue((output / name).is_file(), msg=name)

    def test_ranking_and_agreement_are_optional(self) -> None:
        combined = run_pilot_harness(
            labels_path=_DP / "labels-synthetic.json",
            detections_path=_DP / "detections-synthetic.json",
        )
        self.assertIsNone(combined["agreement"])
        self.assertIsNone(combined["ranking"])
        self.assertIn("RT-001", combined["claim_boundary"])

    def test_require_publishable_fails_closed_on_synthetic(self) -> None:
        exit_code = main(
            [
                "--labels",
                str(_DP / "labels-synthetic.json"),
                "--detections",
                str(_DP / "detections-synthetic.json"),
                "--require-publishable",
            ]
        )
        self.assertEqual(exit_code, 1)


class RankingLabelsTemplateTests(unittest.TestCase):
    def test_template_validates_through_evaluator(self) -> None:
        """The expert-facing template must load as-is (draft, one example
        case, grades 0/1/2) and carry the not-publishable warning."""
        report = evaluate_ranking_quality(_DP / "ranking-labels-template.json")
        self.assertEqual(report["dataset_status"], "draft")
        self.assertEqual(report["case_count"], 1)
        self.assertEqual(report["defined_case_count"], 1)
        self.assertIn("must not be published", report["warning"])
        # Example ordering is priority-consistent with grades → nDCG = 1.
        self.assertAlmostEqual(report["summary"]["ndcg_full"]["point"], 1.0, places=9)

    def test_template_grades_span_full_scale(self) -> None:
        payload = json.loads((_DP / "ranking-labels-template.json").read_text(encoding="utf-8"))
        grades = {row["relevance"] for case in payload["cases"] for row in case["findings"]}
        self.assertEqual(grades, {0, 1, 2})


if __name__ == "__main__":
    unittest.main()
