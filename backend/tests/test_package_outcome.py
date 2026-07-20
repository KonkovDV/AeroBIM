"""Unit tests for PackageOutcome computation and Shared-gate false-green guards."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.package_outcome import compute_package_outcome
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ReportCapabilities,
    RequirementSource,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.domain.package_outcome import PackageOutcome, summary_passed_from_outcome
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.tools.validate_customer_intake_gate import INTAKE_GATE_KEYS


def _caps(**overrides: CapabilityStatus) -> ReportCapabilities:
    fields: dict[str, CapabilityStatus] = {
        "clash": CapabilityStatus(CapabilityState.OK),
        "ids": CapabilityStatus(CapabilityState.OK),
        "ifc_validation": CapabilityStatus(CapabilityState.OK),
        "unit_scale": CapabilityStatus(CapabilityState.OK),
        "raster": CapabilityStatus(CapabilityState.OK),
        "ifc_schema": CapabilityStatus(CapabilityState.OK),
        "calculation_match": CapabilityStatus(CapabilityState.OK),
        "quantity": CapabilityStatus(CapabilityState.OK),
        "mep_system_clash": CapabilityStatus(CapabilityState.OK),
    }
    fields.update(overrides)
    return ReportCapabilities(**fields)


class PackageOutcomeMatrixTests(unittest.TestCase):
    def test_pass_and_warnings(self) -> None:
        caps = _caps()
        policy = build_signoff_policy(profile="development")
        self.assertEqual(
            compute_package_outcome(
                error_count=0,
                warning_count=0,
                capabilities=caps,
                intake_blocked=False,
                policy=policy,
            ),
            PackageOutcome.PASS,
        )
        self.assertEqual(
            compute_package_outcome(
                error_count=0,
                warning_count=2,
                capabilities=caps,
                intake_blocked=False,
                policy=policy,
            ),
            PackageOutcome.PASS_WITH_WARNINGS,
        )

    def test_failed_and_blocked_and_review(self) -> None:
        caps = _caps()
        policy = build_signoff_policy(profile="development")
        self.assertEqual(
            compute_package_outcome(
                error_count=1,
                warning_count=0,
                capabilities=caps,
                intake_blocked=False,
                policy=policy,
            ),
            PackageOutcome.FAILED,
        )
        self.assertEqual(
            compute_package_outcome(
                error_count=0,
                warning_count=0,
                capabilities=caps,
                intake_blocked=True,
                policy=policy,
            ),
            PackageOutcome.BLOCKED,
        )
        self.assertEqual(
            compute_package_outcome(
                error_count=0,
                warning_count=0,
                capabilities=caps,
                intake_blocked=False,
                hitl_requires_review=True,
                policy=policy,
            ),
            PackageOutcome.REVIEW_REQUIRED,
        )

    def test_hard_profile_required_cap_blocks(self) -> None:
        caps = _caps(
            mep_system_clash=CapabilityStatus(CapabilityState.NOT_VERIFIED, "MEP not configured")
        )
        policy = build_signoff_policy(profile="samolet_pilot")
        outcome = compute_package_outcome(
            error_count=0,
            warning_count=0,
            capabilities=caps,
            intake_blocked=False,
            policy=policy,
        )
        self.assertEqual(outcome, PackageOutcome.BLOCKED)

    def test_intake_blocked_dominates_errors(self) -> None:
        caps = _caps()
        outcome = compute_package_outcome(
            error_count=3,
            warning_count=0,
            capabilities=caps,
            intake_blocked=True,
            policy=build_signoff_policy(profile="samolet_pilot"),
        )
        self.assertEqual(outcome, PackageOutcome.BLOCKED)
        self.assertFalse(summary_passed_from_outcome(outcome))

    def test_summary_passed_from_outcome(self) -> None:
        self.assertTrue(summary_passed_from_outcome(PackageOutcome.PASS))
        self.assertTrue(summary_passed_from_outcome(PackageOutcome.PASS_WITH_WARNINGS))
        self.assertFalse(summary_passed_from_outcome(PackageOutcome.BLOCKED))
        self.assertFalse(summary_passed_from_outcome(PackageOutcome.FAILED))
        self.assertFalse(summary_passed_from_outcome(PackageOutcome.REVIEW_REQUIRED))

    def test_serialization_roundtrip(self) -> None:
        summary = ValidationSummary(
            requirement_count=1,
            issue_count=0,
            error_count=0,
            warning_count=0,
            passed=True,
            outcome=PackageOutcome.PASS_WITH_WARNINGS,
        )
        payload = asdict(summary)
        self.assertEqual(payload["outcome"], PackageOutcome.PASS_WITH_WARNINGS)
        # JSON path uses enum value string.
        encoded = json.loads(json.dumps(payload, default=lambda o: getattr(o, "value", o)))
        self.assertEqual(encoded["outcome"], "pass_with_warnings")
        restored = PackageOutcome(encoded["outcome"])
        self.assertEqual(restored, PackageOutcome.PASS_WITH_WARNINGS)


class PackageOutcomeFalseGreenTests(unittest.TestCase):
    def test_intake_blocked_cannot_yield_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            gate = root / "gate.json"
            gate.write_text(
                json.dumps(
                    {
                        "artifact_type": "customer_intake_gate",
                        "status": "BLOCKED_NO_CUSTOMER_DATA",
                        "claim_level": "not_ready",
                        "gates": {key: False for key in INTAKE_GATE_KEYS},
                        "rules": {
                            "llm_assist_counts_as_adjudicator": False,
                            "synthetic_f1_is_product_accuracy": False,
                            "fixture_sla_is_customer_sla": False,
                            "customer_approved_without_approval_ref": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            uc = AnalyzeProjectPackageUseCase(
                requirement_extractor=StructuredRequirementExtractor(),
                narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
                drawing_analyzer=StructuredDrawingAnalyzer(),
                ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=InMemoryAuditStore(),
                signoff_profile="samolet_pilot",
                customer_intake_gate_path=gate,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="outcome-intake-block",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        self.assertEqual(report.summary.outcome, PackageOutcome.BLOCKED)
        self.assertFalse(report.summary.passed)
        self.assertFalse(
            summary_passed_from_outcome(report.summary.outcome or PackageOutcome.FAILED)
        )


if __name__ == "__main__":
    unittest.main()
