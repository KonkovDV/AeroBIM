"""RT-HYPER Phase 1–3 regression: capability policy, audit, HITL determinism."""

from __future__ import annotations

import math
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.capability_policy import (
    build_signoff_policy,
    normalize_signoff_profile,
)
from aerobim.application.services.signoff_policy import summary_passed_after_capabilities
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.drawing_region_hitl import (
    mark_regions_for_hitl,
    review_events_for_hitl_regions,
    validate_bbox_xyxy,
)
from aerobim.domain.mep import MepSystemGraph
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingAnnotation,
    DrawingRegionRef,
    ProblemZone,
    ReportCapabilities,
    RequirementSource,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    AuditEventCorruptionError,
    FilesystemReviewEventStore,
)
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


def _minimal_report(*, report_id: str, ifc_path: Path) -> ValidationReport:
    return ValidationReport(
        report_id=report_id,
        request_id="hyper-audit",
        ifc_path=ifc_path,
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=0,
            error_count=0,
            warning_count=0,
            passed=True,
        ),
    )


class CapabilityPolicyHyperTests(unittest.TestCase):
    def test_samolet_pilot_defaults_require_mep(self) -> None:
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertTrue(policy.require_mep_system_clash)
        self.assertTrue(policy.require_clash)
        self.assertTrue(policy.audit_fail_closed)

    def test_require_mep_blocks_not_verified(self) -> None:
        caps = ReportCapabilities(
            mep_system_clash=CapabilityStatus(
                CapabilityState.NOT_VERIFIED, "customer scope missing"
            ),
        )
        self.assertTrue(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=caps,
                require_mep_system_clash=False,
            )
        )
        self.assertFalse(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=caps,
                require_mep_system_clash=True,
            )
        )

    def test_require_mep_only_ok_passes(self) -> None:
        caps = ReportCapabilities(
            mep_system_clash=CapabilityStatus(CapabilityState.OK, "federated scope verified"),
        )
        self.assertTrue(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=caps,
                require_mep_system_clash=True,
            )
        )

    def test_profile_aliases(self) -> None:
        self.assertEqual(normalize_signoff_profile("samolet"), "samolet_pilot")
        self.assertEqual(normalize_signoff_profile("prod"), "production")

    def test_uc_require_mep_blocks_empty_graph_not_verified(self) -> None:
        class _EmptyMep:
            def build(self, ifc_path):  # noqa: ANN001
                return MepSystemGraph(nodes=(), edges=())

        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                mep_system_graph_provider=_EmptyMep(),
                require_mep_system_clash=True,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="hyper-mep-nv",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.mep_system_clash.status, CapabilityState.NOT_VERIFIED)
        self.assertFalse(report.summary.passed)


class ReviewEventIntegrityTests(unittest.TestCase):
    def test_corrupt_line_counted_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            open_store = FilesystemReviewEventStore(root, fail_closed=False)
            region = DrawingRegionRef(
                sheet_id="AR-01",
                bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
                confidence=0.2,
                modality="detector",
            )
            marked = mark_regions_for_hitl((region,), ())
            events = review_events_for_hitl_regions(
                report_id="rpt-a",
                regions=marked,
                created_at="2026-07-18T00:00:00Z",
            )
            open_store.append(events[0])
            path = root / "review-events" / "rpt-a.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("{not-json\n")
            loaded = open_store.list_for_report("rpt-a")
            self.assertEqual(len(loaded), 1)
            self.assertEqual(open_store.last_invalid_line_count, 1)
            self.assertTrue(open_store.last_load_degraded)

            closed = FilesystemReviewEventStore(root, fail_closed=True)
            with self.assertRaises(AuditEventCorruptionError):
                closed.list_for_report("rpt-a")

    def test_deterministic_event_ids_and_dedupe(self) -> None:
        region = DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
            confidence=0.2,
            modality="detector",
        )
        marked = mark_regions_for_hitl((region,), ())
        first = review_events_for_hitl_regions(
            report_id="rpt-dedupe",
            regions=marked,
            created_at="2026-07-18T00:00:00Z",
        )
        second = review_events_for_hitl_regions(
            report_id="rpt-dedupe",
            regions=marked,
            created_at="2026-07-18T00:00:01Z",
        )
        self.assertEqual(first[0].event_id, second[0].event_id)
        self.assertIsNotNone(first[0].idempotency_key)

        with tempfile.TemporaryDirectory() as temporary_directory:
            store = FilesystemReviewEventStore(Path(temporary_directory))
            store.append(first[0])
            store.append(second[0])
            self.assertEqual(len(store.list_for_report("rpt-dedupe")), 1)


class BboxAndIouHonestyTests(unittest.TestCase):
    def test_reject_nan_and_zero_area(self) -> None:
        status, reason = validate_bbox_xyxy((0.0, 0.0, math.nan, 1.0))
        self.assertEqual(status, "invalid")
        self.assertIn("finite", reason or "")
        status2, _ = validate_bbox_xyxy((0.5, 0.5, 0.5, 0.6))
        self.assertEqual(status2, "invalid")

    def test_low_iou_does_not_count_as_match(self) -> None:
        region = DrawingRegionRef(
            sheet_id="AR-01",
            bbox_xyxy=(0.0, 0.0, 1.0, 1.0),
            confidence=0.9,
            modality="detector",
        )
        ann = DrawingAnnotation(
            annotation_id="a1",
            sheet_id="AR-01",
            target_ref="T1",
            measure_name="zone",
            observed_value="1",
            problem_zone=ProblemZone(x=0.95, y=0.95, width=0.05, height=0.05),
        )
        marked = mark_regions_for_hitl((region,), (ann,))
        self.assertTrue(marked[0].hitl_required)
        self.assertEqual(marked[0].hitl_reason, "unmatched_to_ocr_annotations")


class AuditCommitManifestTests(unittest.TestCase):
    def test_save_writes_commit_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            store.save(_minimal_report(report_id="b" * 32, ifc_path=ifc))
            self.assertTrue(store.is_report_committed("b" * 32))
            self.assertEqual(store.list_orphan_report_ids(), [])

    def test_failure_after_materialize_records_orphan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemAuditStore(root)
            ifc = root / "model.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            report = _minimal_report(report_id="d" * 32, ifc_path=ifc)
            original = store._serialize_report

            def _boom(persisted):  # noqa: ANN001
                raise OSError("disk full during report serialize")

            store._serialize_report = _boom  # type: ignore[method-assign]
            with self.assertRaises(OSError):
                store.save(report)
            store._serialize_report = original  # type: ignore[method-assign]
            self.assertIn("d" * 32, store.list_orphan_report_ids())
            self.assertFalse(store.is_report_committed("d" * 32))


if __name__ == "__main__":
    unittest.main()
