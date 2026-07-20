"""Pilot customer-intake fail-closed on samolet_pilot analyze path."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.customer_intake import CustomerIntakeGate
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import RequirementSource, ValidationRequest
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.tools.validate_customer_intake_gate import (
    INTAKE_GATE_KEYS,
    validate_customer_intake_gate,
)


def _all_false_gates() -> dict[str, bool]:
    return {key: False for key in INTAKE_GATE_KEYS}


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_type": "customer_intake_gate",
        "status": "BLOCKED_NO_CUSTOMER_DATA",
        "claim_level": "not_ready",
        "gates": _all_false_gates(),
        "rules": {
            "llm_assist_counts_as_adjudicator": False,
            "synthetic_f1_is_product_accuracy": False,
            "fixture_sla_is_customer_sla": False,
            "customer_approved_without_approval_ref": False,
        },
    }
    payload.update(overrides)
    return payload


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base: dict[str, object] = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class CustomerIntakeEvaluateTests(unittest.TestCase):
    def test_default_repo_gate_is_blocked(self) -> None:
        result = CustomerIntakeGate.evaluate(CustomerIntakeGate.default_path())
        self.assertFalse(result.ok)
        self.assertTrue(result.reasons)
        self.assertTrue(
            any("intake" in reason.lower() or "gate" in reason.lower() for reason in result.reasons)
        )
        self.assertEqual(result.true_gates, [])

    def test_altered_hash_rejected_by_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_dir = root / "audit" / "evidence"
            evidence_dir.mkdir(parents=True)
            evidence = evidence_dir / "nda.txt"
            body = b"signed-nda"
            evidence.write_bytes(body)
            digest = hashlib.sha256(body).hexdigest()
            # Flip last nibble so digest is still 64 hex but wrong.
            bad_digest = digest[:-1] + ("0" if digest[-1] != "0" else "1")
            gates = _all_false_gates()
            gates["nda_signed"] = True
            path = evidence_dir / "gate.json"
            path.write_text(
                json.dumps(
                    _base_payload(
                        status="IN_PROGRESS",
                        gates=gates,
                        evidence={"nda_signed": {"path": "nda.txt", "sha256": bad_digest}},
                    )
                ),
                encoding="utf-8",
            )
            report = validate_customer_intake_gate(path)
            self.assertFalse(report["ok"])
            self.assertTrue(any("sha256 mismatch" in err for err in report["errors"]))
            intake = CustomerIntakeGate.evaluate(path)
            self.assertFalse(intake.ok)
            self.assertTrue(any("sha256 mismatch" in reason for reason in intake.reasons))


class PilotIntakeEnforcementTests(unittest.TestCase):
    def test_samolet_pilot_false_gates_block_analyze(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            gate = root / "gate.json"
            gate.write_text(json.dumps(_base_payload()), encoding="utf-8")
            uc = _minimal_uc(
                signoff_profile="samolet_pilot",
                customer_intake_gate_path=gate,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="intake-false-gates",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        self.assertFalse(report.summary.passed)
        intake_issues = [
            issue for issue in report.issues if issue.rule_id == "AEROBIM-CUSTOMER-INTAKE"
        ]
        self.assertEqual(len(intake_issues), 1)
        self.assertEqual(intake_issues[0].severity.value, "error")
        self.assertIn("intake", intake_issues[0].message.lower())
        self.assertIn("mep_federated_scope", intake_issues[0].message)

    def test_development_profile_skips_intake_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            gate = root / "gate.json"
            gate.write_text(json.dumps(_base_payload()), encoding="utf-8")
            uc = _minimal_uc(
                signoff_profile="development",
                customer_intake_gate_path=gate,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="intake-dev-skip",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        intake_issues = [
            issue for issue in report.issues if issue.rule_id == "AEROBIM-CUSTOMER-INTAKE"
        ]
        self.assertEqual(intake_issues, [])

    def test_one_adjudicator_true_without_evidence_blocks_analyze(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            gates = _all_false_gates()
            gates["dual_human_adjudicators_named"] = True
            gate = root / "gate.json"
            gate.write_text(
                json.dumps(_base_payload(status="IN_PROGRESS", gates=gates)),
                encoding="utf-8",
            )
            uc = _minimal_uc(
                signoff_profile="samolet_pilot",
                customer_intake_gate_path=gate,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="intake-one-adj",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        self.assertFalse(report.summary.passed)
        intake_issues = [
            issue for issue in report.issues if issue.rule_id == "AEROBIM-CUSTOMER-INTAKE"
        ]
        self.assertEqual(len(intake_issues), 1)
        message = intake_issues[0].message.lower()
        self.assertTrue(
            "dual_human_adjudicators_named" in message or "evidence" in message,
            msg=intake_issues[0].message,
        )

    def test_mep_federated_scope_false_surfaces_in_intake_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            gate = root / "gate.json"
            gate.write_text(json.dumps(_base_payload()), encoding="utf-8")
            intake = CustomerIntakeGate.evaluate(gate)
            self.assertFalse(intake.ok)
            joined = " ".join(intake.reasons)
            self.assertIn("mep_federated_scope", joined)
            uc = _minimal_uc(
                signoff_profile="samolet_pilot",
                customer_intake_gate_path=gate,
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="intake-mep-scope",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        self.assertFalse(report.summary.passed)
        intake_issues = [
            issue for issue in report.issues if issue.rule_id == "AEROBIM-CUSTOMER-INTAKE"
        ]
        self.assertTrue(intake_issues)
        self.assertIn("mep_federated_scope", intake_issues[0].message)


if __name__ == "__main__":
    unittest.main()
