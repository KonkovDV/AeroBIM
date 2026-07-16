from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.evaluate_detection_precision import (
    evaluate_detection_precision,
    main,
    threshold_failures,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "samples" / "benchmarks" / "detection-precision"
LABELS = FIXTURE_DIR / "labels-synthetic.json"
DETECTIONS = FIXTURE_DIR / "detections-synthetic.json"


class DetectionPrecisionHarnessTests(unittest.TestCase):
    def test_computes_exact_micro_and_per_class_counts(self) -> None:
        report = evaluate_detection_precision(LABELS, DETECTIONS)

        self.assertEqual(
            report["micro"],
            {
                "tp": 4,
                "fp": 2,
                "fn": 2,
                "precision": 0.666667,
                "recall": 0.666667,
                "f1": 0.666667,
            },
        )
        self.assertEqual(report["labels"]["excluded"], 1)
        self.assertEqual(report["labels"]["unresolved"], 1)
        self.assertEqual(report["per_class"]["missing-element"]["fn"], 2)
        self.assertEqual(len(report["false_positives"]), 2)
        self.assertEqual(len(report["false_negatives"]), 2)

    def test_synthetic_fixture_never_passes_publishable_protocol_gate(self) -> None:
        report = evaluate_detection_precision(LABELS, DETECTIONS)

        self.assertFalse(report["publishable_protocol_gate"])
        self.assertIn("not adjudicated customer evidence", report["warning"])
        with self.assertRaisesRegex(ValueError, "publishable adjudication protocol gate"):
            evaluate_detection_precision(LABELS, DETECTIONS, require_publishable=True)

    def test_two_adjudicator_protocol_gate_can_be_enforced(self) -> None:
        payload = json.loads(LABELS.read_text(encoding="utf-8"))
        payload["dataset_status"] = "adjudicated"
        payload["adjudication"]["adjudicators"] = [
            {"id": "engineer-1", "role": "AR adjudicator"},
            {"id": "engineer-2", "role": "BIM adjudicator"},
        ]
        unresolved = payload["cases"][0]["expected_findings"][4]
        unresolved["adjudication_status"] = "excluded"
        agreement = {
            "artifact_type": "adjudicator_agreement",
            "schema_version": "1.1.0",
            "cohen_kappa": 0.82,
            "pass_threshold_0_60": True,
            "krippendorff_alpha": 0.79,
            "pass_alpha_0_67": True,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            labels_path = Path(temporary_directory) / "labels.json"
            agreement_path = Path(temporary_directory) / "agreement.json"
            labels_path.write_text(json.dumps(payload), encoding="utf-8")
            agreement_path.write_text(json.dumps(agreement), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "PrecisionClaim is not publishable"):
                evaluate_detection_precision(
                    labels_path,
                    DETECTIONS,
                    require_publishable=True,
                )
            report = evaluate_detection_precision(
                labels_path,
                DETECTIONS,
                require_publishable=True,
                agreement_path=agreement_path,
            )

        self.assertTrue(report["publishable_protocol_gate"])
        self.assertEqual(report["adjudicator_count"], 2)
        self.assertTrue(report["precision_claim"]["publishable"])
        self.assertIsNone(report["warning"])

    def test_threshold_failures_are_ci_friendly(self) -> None:
        report = evaluate_detection_precision(LABELS, DETECTIONS)

        self.assertEqual(
            threshold_failures(
                report,
                min_precision=0.7,
                min_recall=0.6,
                min_f1=0.7,
            ),
            [
                "micro precision 0.666667 < required 0.700000",
                "micro f1 0.666667 < required 0.700000",
            ],
        )

    def test_cli_writes_atomic_report_and_returns_gate_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "evaluation.json"
            exit_code = main(
                [
                    "--labels",
                    str(LABELS),
                    "--detections",
                    str(DETECTIONS),
                    "--min-precision",
                    "0.6",
                    "--min-recall",
                    "0.6",
                    "--output",
                    str(output),
                ]
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["gate"]["passed"])

    def test_duplicate_detection_identity_is_rejected(self) -> None:
        payload = json.loads(DETECTIONS.read_text(encoding="utf-8"))
        payload["cases"][0]["findings"].append(dict(payload["cases"][0]["findings"][0]))
        with tempfile.TemporaryDirectory() as temporary_directory:
            detections_path = Path(temporary_directory) / "detections.json"
            detections_path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate detection identity"):
                evaluate_detection_precision(LABELS, detections_path)


if __name__ == "__main__":
    unittest.main()
