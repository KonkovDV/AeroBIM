from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.ids_assist_boundary import StubIdsAssistDraftAdapter
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.architecture import (
    Contour,
    EvidenceProvenance,
    PrecisionClaim,
    assert_precision_publishable,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    GeneratedRemark,
    ReportCapabilities,
    RequirementSource,
    ValidationRequest,
)
from aerobim.domain.system_capabilities import assert_honesty_capabilities_not_silently_ok
from aerobim.tools.generate_tz_matrix_status import generate_tz_matrix_status


class ArchitectureSeamTests(unittest.TestCase):
    def test_precision_claim_blocks_non_customer_publish(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.95,
            corpus_id="synthetic-x",
            corpus_kind="synthetic",
            adjudicators=0,
            date="2026-07-16",
        )
        self.assertFalse(claim.publishable)
        self.assertIn("withheld", claim.render_value())
        with self.assertRaisesRegex(ValueError, "not publishable"):
            assert_precision_publishable(claim)

    def test_precision_claim_allows_customer_with_two_adjudicators(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.91,
            corpus_id="customer-1",
            corpus_kind="customer",
            adjudicators=2,
            date="2026-07-16",
        )
        self.assertTrue(claim.publishable)
        self.assertIn("0.9100", claim.render_value())
        assert_precision_publishable(claim)

    def test_self_audit_cannot_display_as_external(self) -> None:
        provenance = EvidenceProvenance(
            author_relationship="self",
            label="April 2026 external academic audit",
        )
        self.assertEqual(provenance.display_label(), "internal self-audit")

    def test_tz_matrix_generator_marks_mep_missing(self) -> None:
        payload = generate_tz_matrix_status()
        mep = next(row for row in payload["rows"] if "MEP" in row["requirement"])
        self.assertEqual(mep["status"], "missing")
        self.assertEqual(payload["author_relationship"], "self")

    def test_honesty_capabilities_never_silently_ok(self) -> None:
        caps = ReportCapabilities()
        assert_honesty_capabilities_not_silently_ok(caps)
        self.assertEqual(caps.dwg_dxf.status, CapabilityState.MISSING)
        self.assertEqual(caps.cv_human_level.status, CapabilityState.MISSING)
        self.assertEqual(caps.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        self.assertEqual(
            caps.calculation_correctness.status, CapabilityState.NOT_IMPLEMENTED
        )
        with self.assertRaises(AssertionError):
            assert_honesty_capabilities_not_silently_ok(
                ReportCapabilities(
                    dwg_dxf=CapabilityStatus(CapabilityState.OK, "fake"),
                )
            )

    def test_advisory_off_equals_advisory_on_for_summary_passed(self) -> None:
        """AI advisory contour must not mutate deterministic summary.passed."""

        class _Empty:
            def extract(self, _source):
                return []

            def synthesize(self, _source):
                return []

            def analyze(self, _source):
                return []

        class _Remark:
            def generate(self, issue):
                return GeneratedRemark(title=issue.rule_id, body=issue.message)

        class _Store:
            def __init__(self) -> None:
                self.report = None

            def save(self, report):
                self.report = report
                return report.report_id

            def get(self, report_id):
                if self.report is not None and self.report.report_id == report_id:
                    return self.report
                return None

        def _build() -> AnalyzeProjectPackageUseCase:
            empty = _Empty()
            return AnalyzeProjectPackageUseCase(
                requirement_extractor=empty,
                narrative_rule_synthesizer=empty,
                drawing_analyzer=empty,
                ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
                ids_validator=MagicMock(validate=MagicMock(return_value=[])),
                remark_generator=_Remark(),
                audit_report_store=_Store(),
            )

        request = ValidationRequest(
            request_id="adv-iso",
            ifc_path=Path("synthetic.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
        )
        off = _build().execute(request)
        # Advisory contour call (IDS assist stub) must not affect the next analyze pass.
        StubIdsAssistDraftAdapter().draft_from_narrative("wall fire rating")
        on = _build().execute(request)
        self.assertEqual(off.summary.passed, on.summary.passed)
        self.assertEqual(Contour.AI_ADVISORY.value, "ai_advisory")


class ExportRuntimeBaselineTests(unittest.TestCase):
    def test_export_writes_metrics(self) -> None:
        from aerobim.tools.export_runtime_baseline import export_runtime_baseline

        backend = Path(__file__).resolve().parents[1]
        baseline = export_runtime_baseline(backend_root=backend)
        metrics = baseline["metrics"]
        self.assertGreater(int(metrics["backend_src_loc"]), 1000)
        self.assertGreater(int(metrics["backend_test_functions"]), 100)
        self.assertIn("readme_snippet", baseline)


if __name__ == "__main__":
    unittest.main()
