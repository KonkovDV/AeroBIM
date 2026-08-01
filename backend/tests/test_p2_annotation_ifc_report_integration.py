"""P2-04 integration: annotation_ifc_links confirmed on persisted analyze report."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import DrawingSource, RequirementSource, SourceKind, ValidationRequest
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

REPO = Path(__file__).resolve().parents[2]
WALL_IFC = REPO / "samples" / "ifc" / "wall-pset-qto-pass.ifc"
DRAWING = REPO / "samples" / "drawings" / "wall-pset-annotation-with-guid.txt"
REQ = REPO / "samples" / "requirements" / "techlab-demo-rules.txt"
WALL_GUID = "3ZAR7ASd14MuxcHc7_fqIb"
BOGUS_GUID = "ZZZZZZZZZZZZZZZZZZZZZZ"


class AnnotationIfcReportIntegrationTests(unittest.TestCase):
    def test_analyze_confirms_claimed_guid_on_persisted_report(self) -> None:
        if not WALL_IFC.exists() or not DRAWING.exists():
            self.skipTest("fixture IFC/drawing missing")
        try:
            import ifcopenshell  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("ifcopenshell not installed")

        store = InMemoryAuditStore()
        uc = AnalyzeProjectPackageUseCase(
            requirement_extractor=StructuredRequirementExtractor(),
            narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
            drawing_analyzer=StructuredDrawingAnalyzer(),
            ifc_validator=IfcOpenShellValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )
        report = uc.execute(
            ValidationRequest(
                request_id="p2-04-annotation-report",
                ifc_path=WALL_IFC,
                requirement_source=RequirementSource(
                    text=REQ.read_text(encoding="utf-8"),
                    path=REQ,
                    source_kind=SourceKind.STRUCTURED_TEXT,
                    source_id="fixture-req",
                ),
                drawing_sources=(
                    DrawingSource(
                        text=DRAWING.read_text(encoding="utf-8"),
                        path=DRAWING,
                        sheet_id="AR-01",
                        format="text",
                    ),
                ),
            )
        )

        self.assertGreaterEqual(len(report.annotation_ifc_links), 1)
        by_id = {str(link.get("annotation_id")): link for link in report.annotation_ifc_links}
        ok = by_id.get("WALL-GUID-OK")
        bad = by_id.get("WALL-GUID-BAD")
        self.assertIsNotNone(ok)
        self.assertIsNotNone(bad)
        assert ok is not None and bad is not None
        self.assertEqual(ok.get("ifc_guid"), WALL_GUID)
        self.assertIn("claimed_guid:", str(ok.get("evidence_ref")))
        self.assertIsNone(bad.get("ifc_guid"))
        self.assertIn(f"claimed_guid:{BOGUS_GUID}", str(bad.get("evidence_ref")))

        reloaded = store.get(report.report_id)
        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(reloaded.annotation_ifc_links, report.annotation_ifc_links)


if __name__ == "__main__":
    unittest.main()
