"""Wave 2 tails + Wave 3 — bSI cert, report filters, review KPI, LOIN levels."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.ids_assist_boundary import StubIdsAssistDraftAdapter
from aerobim.application.services.loin_metadata_resolver import LoinMetadataResolver
from aerobim.application.services.report_list_filters import apply_report_list_filters
from aerobim.application.services.review_kpi import summarize_review_events
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    ReportListFilters,
    ReportSummaryEntry,
    ReviewEvent,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.bsi_validation_service import (
    HttpBsiValidationService,
    LocalSchemaPackCertificate,
)
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class ReportListFilterTests(unittest.TestCase):
    def test_apply_filters_by_project_and_passed(self) -> None:
        entries = [
            ReportSummaryEntry(
                "a" * 32, "r1", "t1", True, 0, project_name="Alpha", discipline="AR"
            ),
            ReportSummaryEntry(
                "b" * 32, "r2", "t2", False, 2, project_name="Beta", discipline="ME"
            ),
        ]
        filtered = apply_report_list_filters(entries, ReportListFilters(project="alp", passed=True))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].report_id, "a" * 32)


class BsiValidationServiceTests(unittest.TestCase):
    def test_http_client_returns_public_id(self) -> None:
        def fake_submit(url, file_name, payload, token, timeout):
            self.assertIn("/api/v1/validationrequest", url)
            self.assertEqual(token, "tok")
            self.assertEqual(file_name, "model.ifc")
            self.assertEqual(payload, b"ISO-10303-21;")
            return {"public_id": "bsi-public-123"}

        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_bytes(b"ISO-10303-21;")
            client = HttpBsiValidationService(
                base_url="https://dev.validate.buildingsmart.org",
                api_token="tok",
                http_submit=fake_submit,
            )
            self.assertEqual(client.submit(ifc), "bsi-public-123")

    def test_local_pack_certificate_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_bytes(b"ISO-10303-21;")
            cert = LocalSchemaPackCertificate(pack_id="pack-v1")
            self.assertEqual(cert.submit(ifc), f"pack-v1:model.ifc:{ifc.stat().st_size}")

    def test_analyze_attaches_schema_request_id(self) -> None:
        from aerobim.domain.models import RequirementSource
        from aerobim.infrastructure.adapters.docling_requirement_extractor import (
            StructuredRequirementExtractor,
        )

        class _FakeIfc:
            def validate(self, ifc_path, requirements):
                return []

        class _FakeBsi:
            def submit(self, ifc_path):
                return "local-cert-99"

        with tempfile.TemporaryDirectory() as tmp:
            ifc = Path(tmp) / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            use_case = AnalyzeProjectPackageUseCase(
                requirement_extractor=StructuredRequirementExtractor(),
                narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
                drawing_analyzer=StructuredDrawingAnalyzer(),
                ifc_validator=_FakeIfc(),
                remark_generator=TemplateRemarkGenerator(),
                audit_report_store=InMemoryAuditStore(),
                bsi_validation_service=_FakeBsi(),
            )
            report = use_case.execute(
                ValidationRequest(
                    request_id="req",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    ),
                )
            )
            self.assertEqual(report.schema_validation_request_id, "local-cert-99")
            assert report.capabilities is not None
            self.assertEqual(report.capabilities.ifc_schema.external_ref, "local-cert-99")
            self.assertEqual(report.capabilities.ifc_schema.status, CapabilityState.NOT_VERIFIED)


class ReviewEventTests(unittest.TestCase):
    def test_filesystem_store_and_kpi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp))
            event = ReviewEvent(
                event_id="e1",
                report_id="c" * 32,
                event_type="accepted",
                created_at="2026-07-10T12:00:00+00:00",
                latency_ms=1200,
            )
            store.append(event)
            store.append(
                ReviewEvent(
                    event_id="e2",
                    report_id="c" * 32,
                    event_type="rejected",
                    created_at="2026-07-10T12:01:00+00:00",
                    latency_ms=800,
                )
            )
            events = store.list_for_report("c" * 32)
            self.assertEqual(len(events), 2)
            kpi = summarize_review_events(events)
            self.assertEqual(kpi["event_count"], 2)
            self.assertEqual(kpi["acceptance_rate"], 0.5)
            self.assertEqual(kpi["avg_latency_ms"], 1000.0)


class LoinInformationLevelTests(unittest.TestCase):
    def test_geometry_level_for_clash_prefix(self) -> None:
        resolver = LoinMetadataResolver()
        meta = resolver.resolve("CLASH-HARD-001")
        self.assertIsNotNone(meta)
        assert meta is not None
        self.assertEqual(meta.information_level, "geometry")


class SpatialPredicateTests(unittest.TestCase):
    def test_hard_clash_is_warning_unless_affects_pass(self) -> None:
        from aerobim.application.services.spatial_predicates import issues_from_clash_results
        from aerobim.domain.models import ClashResult, FindingCategory, Severity

        clash = ClashResult(
            element_a_guid="a",
            element_b_guid="b",
            clash_type="hard",
            distance=0.01,
            description="pipe vs duct",
        )
        soft = issues_from_clash_results([clash], affects_pass=False)
        self.assertEqual(soft[0].severity, Severity.WARNING)
        self.assertEqual(soft[0].category, FindingCategory.SPATIAL)
        hard = issues_from_clash_results([clash], affects_pass=True)
        self.assertEqual(hard[0].severity, Severity.ERROR)


class IdsAssistBoundaryTests(unittest.TestCase):
    def test_stub_is_advisory_only(self) -> None:
        draft = StubIdsAssistDraftAdapter().draft_from_narrative("Walls shall have FireRating")
        self.assertTrue(draft.advisory_only)
        self.assertEqual(draft.suggested_ids_xml, "")


if __name__ == "__main__":
    unittest.main()
