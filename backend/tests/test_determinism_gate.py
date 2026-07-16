from __future__ import annotations

import unittest

from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue


class DeterminismGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = DeterminismGate()

    def test_engine_only_passthrough(self) -> None:
        engine = [
            ValidationIssue(
                rule_id="ENG-1",
                severity=Severity.ERROR,
                message="wall missing",
                category=FindingCategory.IFC_VALIDATION,
                finding_id="f1",
            )
        ]
        merged, divergences = self.gate.reconcile(engine_issues=engine, advisory_issues=())
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].severity, Severity.ERROR)
        self.assertEqual(divergences, ())

    def test_advisory_only_demoted_to_info(self) -> None:
        advisory = [
            ValidationIssue(
                rule_id="AI-1",
                severity=Severity.ERROR,
                message="hallucinated clash",
                category=FindingCategory.SPATIAL,
                finding_id="a1",
            )
        ]
        merged, divergences = self.gate.reconcile(engine_issues=(), advisory_issues=advisory)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].severity, Severity.INFO)
        self.assertIn("advisory-only", merged[0].message)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergences[0].resolution, "engine_wins")

    def test_divergence_keeps_engine_and_emits_warning(self) -> None:
        engine = [
            ValidationIssue(
                rule_id="ENG-1",
                severity=Severity.WARNING,
                message="clearance 50mm",
                finding_id="same",
            )
        ]
        advisory = [
            ValidationIssue(
                rule_id="ENG-1",
                severity=Severity.ERROR,
                message="clearance 5mm",
                finding_id="same",
            )
        ]
        merged, divergences = self.gate.reconcile(engine_issues=engine, advisory_issues=advisory)
        self.assertTrue(
            any(i.rule_id == "ENG-1" and i.severity is Severity.WARNING for i in merged)
        )
        self.assertTrue(any(i.rule_id == "AEROBIM-DETERMINISM-DIVERGENCE" for i in merged))
        self.assertEqual(len(divergences), 1)
        self.assertIn("warning", divergences[0].engine_verdict)

    def test_divergence_record_is_domain_serializable(self) -> None:
        from dataclasses import asdict

        from aerobim.domain.models import DivergenceRecord

        record = DivergenceRecord(
            finding_key="f1",
            engine_verdict="absent",
            advisory_verdict="error:hallucinated",
        )
        payload = asdict(record)
        self.assertEqual(payload["resolution"], "engine_wins")
        self.assertEqual(payload["finding_key"], "f1")


if __name__ == "__main__":
    unittest.main()
