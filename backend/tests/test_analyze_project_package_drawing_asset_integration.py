from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    DrawingSource,
    ParsedRequirement,
    RequirementSource,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


class _NoOpRequirementExtractor:
    def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-001",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            )
        ]


class _NoOpNarrativeSynthesizer:
    def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return []


class _NoOpDrawingAnalyzer:
    def analyze(self, _source: DrawingSource) -> list:
        return []


class _NoOpVisionDrawingAnalyzer:
    def analyze_image(self, _image_path: Path, sheet_id: str | None = None) -> list:
        return []


class _NoOpIfcValidator:
    def validate(
        self, _ifc_path: Path, _requirements: list[ParsedRequirement]
    ) -> list[ValidationIssue]:
        return []


class _NoOpRemarkGenerator:
    def generate(self, _issue: ValidationIssue):
        return None


class AnalyzeProjectPackageDrawingAssetIntegrationTests(unittest.TestCase):
    def _make_use_case(self, storage_dir: Path) -> AnalyzeProjectPackageUseCase:
        return AnalyzeProjectPackageUseCase(
            requirement_extractor=_NoOpRequirementExtractor(),
            narrative_rule_synthesizer=_NoOpNarrativeSynthesizer(),
            drawing_analyzer=_NoOpDrawingAnalyzer(),
            ifc_validator=_NoOpIfcValidator(),
            ids_validator=None,
            vision_drawing_analyzer=_NoOpVisionDrawingAnalyzer(),
            remark_generator=_NoOpRemarkGenerator(),
            audit_report_store=FilesystemAuditStore(storage_dir),
        )

    def test_execute_persists_multi_page_pdf_drawing_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            pdf_path = storage_dir / "sheet-openrebar.pdf"

            document = pymupdf.open()
            first_page = document.new_page(width=320, height=200)
            first_page.insert_text((24, 40), "WALL-01 thickness 250 mm")
            second_page = document.new_page(width=360, height=240)
            second_page.insert_text((36, 60), "WALL-02 thickness 300 mm")
            document.save(pdf_path)
            document.close()

            use_case = self._make_use_case(storage_dir)

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-pdf-drawing-assets",
                    ifc_path=storage_dir / "model.ifc",
                    requirement_source=RequirementSource(text="REQ-EMPTY"),
                    drawing_sources=(
                        DrawingSource(
                            text="",
                            path=pdf_path,
                            sheet_id="A-101",
                            format="pdf",
                        ),
                    ),
                )
            )

            self.assertEqual(len(report.drawing_assets), 2)
            page_numbers = [asset.page_number for asset in report.drawing_assets]
            self.assertEqual(page_numbers, [1, 2])
            for asset in report.drawing_assets:
                self.assertEqual(asset.sheet_id, "A-101")
                self.assertEqual(asset.media_type, "image/png")
                self.assertIsNone(asset.source_path)
                self.assertIsNotNone(asset.stored_filename)
                self.assertGreater(asset.coordinate_width or 0, 0)
                self.assertGreater(asset.coordinate_height or 0, 0)
                preview_path = (
                    storage_dir / "drawing-assets" / report.report_id / str(asset.stored_filename)
                )
                self.assertTrue(preview_path.exists())

    def test_execute_persists_raster_drawing_asset_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            image_path = storage_dir / "sheet-a201.png"

            pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 120, 60), False)
            pix.set_rect(pix.irect, (255, 255, 255))
            pix.save(image_path)

            use_case = self._make_use_case(storage_dir)

            report = use_case.execute(
                ValidationRequest(
                    request_id="req-raster-drawing-assets",
                    ifc_path=storage_dir / "model.ifc",
                    requirement_source=RequirementSource(text="REQ-EMPTY"),
                    drawing_sources=(
                        DrawingSource(
                            text="",
                            path=image_path,
                            sheet_id="A-201",
                            format="png",
                        ),
                    ),
                )
            )

            self.assertEqual(len(report.drawing_assets), 1)
            asset = report.drawing_assets[0]
            self.assertEqual(asset.sheet_id, "A-201")
            self.assertEqual(asset.page_number, 1)
            self.assertEqual(asset.media_type, "image/png")
            self.assertEqual(asset.coordinate_width, 120)
            self.assertEqual(asset.coordinate_height, 60)
            self.assertIsNone(asset.source_path)
            self.assertIsNotNone(asset.stored_filename)
            preview_path = (
                storage_dir / "drawing-assets" / report.report_id / str(asset.stored_filename)
            )
            self.assertTrue(preview_path.exists())
