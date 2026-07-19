"""Pilot fail-closed gaps not covered by P0 / RT post remediation suites.

Covers: empty/unreadable PDF honesty, requested IDS without validator,
adapter exception → FAILED, partial multi-source coverage honesty.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    CapabilityState,
    DrawingSource,
    RequirementSource,
    Severity,
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


class _EmptyRasterAnalyzer:
    def analyze_image(self, path: Path, *, sheet_id: str | None = None):  # noqa: ANN001
        del path, sheet_id
        return []


class _BoomRasterAnalyzer:
    def analyze_image(self, path: Path, *, sheet_id: str | None = None):  # noqa: ANN001
        del sheet_id
        raise OSError(f"unreadable drawing: {path}")


class _BoomIdsValidator:
    def validate(self, ids_path: Path, ifc_path: Path):  # noqa: ANN001
        del ifc_path
        raise FileNotFoundError(ids_path)


class PilotFailClosedGapTests(unittest.TestCase):
    def test_empty_pdf_zero_yield_is_not_silent_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            pdf = root / "empty.pdf"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
            uc = _minimal_uc(raster_drawing_analyzer=_EmptyRasterAnalyzer())
            report = uc.execute(
                ValidationRequest(
                    request_id="gap-empty-pdf",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=pdf, format="pdf", sheet_id="AR-01"),),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.raster.status, CapabilityState.FAILED)
        self.assertIn("zero annotations", report.capabilities.raster.reason or "")
        self.assertFalse(report.summary.passed)

    def test_unreadable_pdf_adapter_exception_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            pdf = root / "bad.pdf"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            pdf.write_bytes(b"not-a-pdf")
            uc = _minimal_uc(raster_drawing_analyzer=_BoomRasterAnalyzer())
            report = uc.execute(
                ValidationRequest(
                    request_id="gap-unreadable-pdf",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(DrawingSource(path=pdf, format="pdf", sheet_id="AR-02"),),
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.raster.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)

    def test_requested_ids_without_validator_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ids = root / "rules.ids"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            ids.write_text("<ids/>", encoding="utf-8")
            uc = _minimal_uc(ids_validator=None)
            report = uc.execute(
                ValidationRequest(
                    request_id="gap-ids-missing-validator",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    ids_path=ids,
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ids.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)
        self.assertTrue(
            any(
                issue.rule_id == "AEROBIM-IDS-CAPABILITY" and issue.severity is Severity.ERROR
                for issue in report.issues
            )
        )

    def test_ids_adapter_exception_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ids = root / "missing.ids"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            uc = _minimal_uc(ids_validator=_BoomIdsValidator())
            report = uc.execute(
                ValidationRequest(
                    request_id="gap-ids-adapter-boom",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    ids_path=ids,
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ids.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)
        self.assertTrue(
            any(
                issue.rule_id == "AEROBIM-IDS-ERROR" and issue.severity is Severity.ERROR
                for issue in report.issues
            )
        )

    def test_partial_multisource_failed_raster_shows_in_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            pdf = root / "sheet.pdf"
            txt = root / "notes.txt"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")
            txt.write_text(
                "ANN-001|TXT-01|WALL-01|thickness|200|mm|1|10|20|100|50\n",
                encoding="utf-8",
            )
            uc = _minimal_uc(raster_drawing_analyzer=_EmptyRasterAnalyzer())
            report = uc.execute(
                ValidationRequest(
                    request_id="gap-partial-multi",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    drawing_sources=(
                        DrawingSource(path=txt, format="text", sheet_id="TXT-01"),
                        DrawingSource(path=pdf, format="pdf", sheet_id="PDF-01"),
                    ),
                )
            )
        assert report.capabilities is not None
        # Text source may contribute annotations; requested raster with zero OCR
        # yield must still surface as failed (not silent OK for the package).
        self.assertEqual(report.capabilities.raster.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)


if __name__ == "__main__":
    unittest.main()
