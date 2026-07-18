"""Residual P0 hardening: zip bomb, schema round-trip, HITL SM, advisory isolation."""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.services.signoff_policy import summary_passed_after_capabilities
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_bytes
from aerobim.domain.finding_provenance import assert_finding_persistable, ensure_finding_provenance
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    FindingCategory,
    ProblemZone,
    ReportCapabilities,
    RequirementSource,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.domain.review_state_machine import HitlTransitionError, assert_hitl_transition
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class ZipBombGuardTests(unittest.TestCase):
    def test_too_many_members_rejected(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            for index in range(10):
                archive.writestr(f"m{index}.txt", b"x")
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(buf.getvalue(), max_members=5)

    def test_normal_zip_accepted(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("a.txt", b"hello")
        result = inspect_zip_bytes(buf.getvalue())
        self.assertEqual(result.member_count, 1)


class ReportSchemaRoundTripTests(unittest.TestCase):
    def test_save_reload_preserves_provenance_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            issue = ensure_finding_provenance(
                ValidationIssue(
                    rule_id="IDS-WALL-001",
                    severity=Severity.ERROR,
                    message="missing FireRating",
                    category=FindingCategory.IFC_VALIDATION,
                    element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
                    property_set="Pset_WallCommon",
                    property_name="FireRating",
                    source_id="ids-pack",
                    evidence_refs=("ids-pack#ifc:2O2Fr$t4X7Zf8NOew3FLOH",),
                    problem_zone=ProblemZone(sheet_id="AR-01", page_number=1, x=0.1, y=0.2),
                    approval_ref="APPR-TEST-1",
                    tenant_id="tenant-a",
                    project_id="proj-1",
                    finding_id="find-fixed-001",
                )
            )
            assert_finding_persistable(issue)
            report = ValidationReport(
                report_id="e" * 32,
                request_id="round-trip",
                ifc_path=ifc,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(issue,),
                summary=ValidationSummary(0, 1, 1, 0, False),
                tenant_id="tenant-a",
                project_id="proj-1",
                schema_version="1.0.0",
                capabilities=ReportCapabilities(
                    ifc_validation=CapabilityStatus(CapabilityState.FAILED, "ids fail"),
                ),
            )
            store.save(report)
            loaded = store.get(report.report_id)
            assert loaded is not None
            self.assertEqual(loaded.schema_version, "1.0.0")
            self.assertEqual(loaded.tenant_id, "tenant-a")
            self.assertEqual(len(loaded.issues), 1)
            reloaded = loaded.issues[0]
            self.assertEqual(reloaded.finding_id, "find-fixed-001")
            self.assertEqual(reloaded.evidence_refs, ("ids-pack#ifc:2O2Fr$t4X7Zf8NOew3FLOH",))
            self.assertEqual(reloaded.element_guid, "2O2Fr$t4X7Zf8NOew3FLOH")
            self.assertEqual(reloaded.approval_ref, "APPR-TEST-1")
            self.assertEqual(reloaded.property_set, "Pset_WallCommon")
            assert reloaded.problem_zone is not None
            self.assertEqual(reloaded.problem_zone.sheet_id, "AR-01")
            self.assertTrue(store.is_report_committed(report.report_id))


class HitlStateMachineTests(unittest.TestCase):
    def test_allowed_happy_path(self) -> None:
        self.assertEqual(
            assert_hitl_transition(current=None, event_type="escalated"),
            "escalated",
        )
        self.assertEqual(
            assert_hitl_transition(current="escalated", event_type="opened", actor="expert-1"),
            "opened",
        )
        self.assertEqual(
            assert_hitl_transition(
                current="opened",
                event_type="accepted",
                actor="expert-1",
            ),
            "accepted",
        )

    def test_accepted_to_opened_forbidden(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="accepted", event_type="opened", actor="expert-1")

    def test_edited_requires_actor_note_and_rejects_system(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="opened", event_type="edited")
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="opened", event_type="edited", actor="expert-1")
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(
                current="opened",
                event_type="edited",
                actor="system",
                note="diff",
            )
        self.assertEqual(
            assert_hitl_transition(
                current="opened",
                event_type="edited",
                actor="expert-1",
                note="remark clarified",
            ),
            "edited",
        )

    def test_rejected_requires_reason(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="opened", event_type="rejected", actor="expert-1")
        self.assertEqual(
            assert_hitl_transition(
                current="opened",
                event_type="rejected",
                actor="expert-1",
                note="false positive vs sheet AR-01",
            ),
            "rejected",
        )

    def test_waived_requires_reason(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="opened", event_type="waived", actor="expert-1")
        self.assertEqual(
            assert_hitl_transition(
                current="opened",
                event_type="waived",
                actor="expert-1",
                note="customer exception memo X",
            ),
            "waived",
        )


class AdvisoryIsolationTests(unittest.TestCase):
    def test_advisory_only_error_demoted_and_does_not_block_pass(self) -> None:
        gate = DeterminismGate()
        engine = (
            ValidationIssue(
                rule_id="ENG-1",
                severity=Severity.WARNING,
                message="engine warning",
                category=FindingCategory.IFC_VALIDATION,
                finding_id="eng-1",
                source_id="engine",
                evidence_refs=("engine#1",),
            ),
        )
        advisory = (
            ValidationIssue(
                rule_id="ADV-ONLY",
                severity=Severity.ERROR,
                message="llm invented blocker",
                category=FindingCategory.IFC_VALIDATION,
                finding_id="adv-1",
                source_id="ai-advisory",
                evidence_refs=("ai#1",),
            ),
        )
        merged, divergences = gate.reconcile(engine_issues=engine, advisory_issues=advisory)
        self.assertTrue(
            any(i.rule_id == "ADV-ONLY" and i.severity is Severity.INFO for i in merged)
        )
        self.assertTrue(divergences)
        error_count = sum(1 for i in merged if i.severity is Severity.ERROR)
        caps = ReportCapabilities()
        self.assertTrue(
            summary_passed_after_capabilities(error_count=error_count, capabilities=caps)
        )

    def test_use_case_advisory_injection_cannot_force_pass_flip_to_true(self) -> None:
        """Engine ERROR remains authoritative; advisory cannot clear it."""

        engine_error = ValidationIssue(
            rule_id="ENG-ERR",
            severity=Severity.ERROR,
            message="real engine failure",
            category=FindingCategory.IFC_VALIDATION,
            finding_id="eng-err",
            source_id="engine",
            evidence_refs=("engine#err",),
        )
        ifc_validator = MagicMock()
        ifc_validator.validate.return_value = [engine_error]
        advisory_ok = ValidationIssue(
            rule_id="ENG-ERR",
            severity=Severity.WARNING,
            message="ai says soft",
            category=FindingCategory.IFC_VALIDATION,
            finding_id="eng-err",
            source_id="ai-advisory",
            evidence_refs=("ai#err",),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                ifc_validator=ifc_validator,
                advisory_issues=(advisory_ok,),
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="adv-isolation",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        self.assertFalse(report.summary.passed)
        self.assertTrue(
            any(i.severity is Severity.ERROR and i.rule_id == "ENG-ERR" for i in report.issues)
        )
        self.assertTrue(
            any(i.rule_id == "AEROBIM-DETERMINISM-DIVERGENCE" for i in report.issues)
            or any(d.resolution == "engine_wins" for d in report.divergences)
        )


if __name__ == "__main__":
    unittest.main()
