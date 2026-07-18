"""Phase 1 sign-off hardening: required profiles, quantity, schema, raster, clash."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.signoff_policy import summary_passed_after_capabilities
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    DrawingSource,
    ReportCapabilities,
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
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


class Phase1RequiredCapabilityPolicyTests(unittest.TestCase):
    def test_require_clash_blocks_skipped(self) -> None:
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.SKIPPED, "ifcclash missing"),
            ifc_schema=CapabilityStatus(CapabilityState.OK),
            mep_system_clash=CapabilityStatus(CapabilityState.OK),
        )
        self.assertTrue(summary_passed_after_capabilities(error_count=0, capabilities=caps))
        self.assertFalse(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=caps,
                policy=build_signoff_policy(profile="development", require_clash=True),
            )
        )

    def test_require_bsi_schema_blocks_skipped(self) -> None:
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.OK),
            ifc_schema=CapabilityStatus(CapabilityState.SKIPPED, "not configured"),
            mep_system_clash=CapabilityStatus(CapabilityState.OK),
        )
        self.assertFalse(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=caps,
                policy=build_signoff_policy(profile="development", require_bsi_schema=True),
            )
        )

    def test_samolet_pilot_blocks_default_capabilities(self) -> None:
        # Default caps: clash SKIPPED, schema SKIPPED, mep NOT_VERIFIED.
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertFalse(
            summary_passed_after_capabilities(
                error_count=0,
                capabilities=ReportCapabilities(),
                policy=policy,
            )
        )

    def test_quantity_not_verified_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            quantity=CapabilityStatus(CapabilityState.NOT_VERIFIED, "checker missing with claims"),
        )
        self.assertFalse(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_quantity_skipped_does_not_block_in_development(self) -> None:
        caps = ReportCapabilities(
            quantity=CapabilityStatus(CapabilityState.SKIPPED, "not evaluated"),
        )
        self.assertTrue(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_failed_raster_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            raster=CapabilityStatus(CapabilityState.FAILED, "zero annotations"),
        )
        self.assertFalse(summary_passed_after_capabilities(error_count=0, capabilities=caps))


class Phase1UseCaseSignoffTests(unittest.TestCase):
    def test_require_bsi_schema_promotes_missing_validator_to_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(
                require_bsi_schema=True,
                ifc_schema_validator=None,
                require_mep_system_clash=False,
            )
            report = uc.execute(
                ValidationRequest(
                    request_id="p1-schema",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ifc_schema.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)

    def test_raster_requested_without_analyzer_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            pdf = Path(temporary_directory) / "sheet.pdf"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.4")
            uc = _minimal_uc(raster_drawing_analyzer=None)
            report = uc.execute(
                ValidationRequest(
                    request_id="p1-raster",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=pdf, format="pdf", sheet_id="AR-01"),),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.raster.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)

    def test_quantity_claims_without_checker_not_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            ifc = Path(temporary_directory) / "m.ifc"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            # Area-style requirement text that yields quantity claims.
            uc = _minimal_uc(quantity_consistency_checker=None)
            report = uc.execute(
                ValidationRequest(
                    request_id="p1-qty",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text=(
                            "AREA|IFCSPACE|GrossFloorArea|120 m2|src-area\n"
                            "R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                        ),
                    ),
                )
            )
        assert report.capabilities is not None
        # If no area claims extracted, quantity stays SKIPPED (acceptable).
        # When claims present, NOT_VERIFIED must block.
        if report.capabilities.quantity.status is CapabilityState.NOT_VERIFIED:
            self.assertFalse(report.summary.passed)
        else:
            self.assertEqual(
                report.capabilities.quantity.status,
                CapabilityState.SKIPPED,
            )


if __name__ == "__main__":
    unittest.main()
