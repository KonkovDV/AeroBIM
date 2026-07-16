from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.measure_adjudicator_agreement import (
    cohen_kappa,
    krippendorff_alpha_nominal,
    measure_adjudication_csv,
)
from aerobim.tools.validate_customer_intake_gate import validate_customer_intake_gate


class AdjudicatorAgreementTests(unittest.TestCase):
    def test_cohen_kappa_perfect_agreement(self) -> None:
        self.assertEqual(cohen_kappa(["TP", "FP", "FN"], ["TP", "FP", "FN"]), 1.0)

    def test_cohen_kappa_chance_only_is_zero(self) -> None:
        kappa = cohen_kappa(["TP", "TP", "FP", "FP"], ["TP", "FP", "TP", "FP"])
        self.assertAlmostEqual(kappa, 0.0, places=6)

    def test_krippendorff_alpha_perfect(self) -> None:
        units = [["TP", "TP"], ["FP", "FP"], ["FN", "FN"]]
        self.assertEqual(krippendorff_alpha_nominal(units), 1.0)

    def test_template_csv_reports_matrix_kappa_and_alpha(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        csv_path = (
            repo / "samples" / "benchmarks" / "detection-precision" / "adjudication-template.csv"
        )
        self.assertTrue(csv_path.exists())
        payload = measure_adjudication_csv(csv_path)
        self.assertEqual(payload["artifact_type"], "adjudicator_agreement")
        self.assertEqual(payload["schema_version"], "1.1.0")
        self.assertEqual(payload["paired_items"], 4)
        self.assertIn("confusion_matrix", payload)
        self.assertIn("krippendorff_alpha", payload)
        self.assertIn("pass_alpha_0_67", payload)
        self.assertLess(float(payload["cohens_kappa"]), 1.0)

    def test_requires_two_adjudicators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one.csv"
            path.write_text(
                "finding_id,adjudicator_id,verdict\nf1,engineer-a,TP\nf2,engineer-a,FP\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                measure_adjudication_csv(path)


class CustomerIntakeGateValidationTests(unittest.TestCase):
    def test_default_repo_gate_all_false_passes(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        gate = repo / "audit" / "evidence" / "customer-intake-gate.json"
        self.assertTrue(gate.exists())
        report = validate_customer_intake_gate(gate)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["true_gates"], [])
        self.assertEqual(report["checkpoint_hint"], "NO_GO")

    def test_true_gate_without_evidence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gate.json"
            payload = {
                "artifact_type": "customer_intake_gate",
                "status": "IN_PROGRESS",
                "claim_level": "not_ready",
                "gates": {
                    "nda_signed": True,
                    "scope_memo_signed": False,
                    "customer_package_in_samples_customer": False,
                    "customer_approved_norm_pack_with_approval_ref": False,
                    "ids_or_property_table_present": False,
                    "dual_human_adjudicators_named": False,
                    "cohens_kappa_or_krippendorff_alpha_reported": False,
                    "confusion_matrix_reported": False,
                    "zero_unresolved_labels": False,
                    "precision_claim_publishable": False,
                    "cde_bcf_import_evidence": False,
                    "customer_sla_pack_measured": False,
                    "mep_federated_scope": False,
                },
                "rules": {
                    "llm_assist_counts_as_adjudicator": False,
                    "synthetic_f1_is_product_accuracy": False,
                    "fixture_sla_is_customer_sla": False,
                    "customer_approved_without_approval_ref": False,
                },
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_customer_intake_gate(path)
            self.assertFalse(report["ok"])
            self.assertTrue(any("nda_signed" in err for err in report["errors"]))

    def test_blocked_status_forbids_true_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gate.json"
            evidence = Path(tmp) / "nda.txt"
            evidence.write_text("signed", encoding="utf-8")
            payload = {
                "artifact_type": "customer_intake_gate",
                "status": "BLOCKED_NO_CUSTOMER_DATA",
                "claim_level": "not_ready",
                "gates": {
                    "nda_signed": True,
                    "scope_memo_signed": False,
                    "customer_package_in_samples_customer": False,
                    "customer_approved_norm_pack_with_approval_ref": False,
                    "ids_or_property_table_present": False,
                    "dual_human_adjudicators_named": False,
                    "cohens_kappa_or_krippendorff_alpha_reported": False,
                    "confusion_matrix_reported": False,
                    "zero_unresolved_labels": False,
                    "precision_claim_publishable": False,
                    "cde_bcf_import_evidence": False,
                    "customer_sla_pack_measured": False,
                    "mep_federated_scope": False,
                },
                "rules": {
                    "llm_assist_counts_as_adjudicator": False,
                    "synthetic_f1_is_product_accuracy": False,
                    "fixture_sla_is_customer_sla": False,
                    "customer_approved_without_approval_ref": False,
                },
                "evidence": {"nda_signed": str(evidence)},
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_customer_intake_gate(path)
            self.assertFalse(report["ok"])
            self.assertTrue(any("BLOCKED_NO_CUSTOMER_DATA" in err for err in report["errors"]))


if __name__ == "__main__":
    unittest.main()
