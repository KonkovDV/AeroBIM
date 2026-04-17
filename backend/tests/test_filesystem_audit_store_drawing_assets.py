from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

import pymupdf

from aerobim.domain.models import DrawingAsset, ValidationReport, ValidationSummary
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore


class FilesystemAuditStoreDrawingAssetTests(unittest.TestCase):
    def test_save_materializes_pdf_page_preview_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            pdf_path = storage_dir / "source-sheet.pdf"

            document = pymupdf.open()
            page = document.new_page(width=320, height=200)
            page.insert_text((24, 40), "WALL-01 thickness 250 mm")
            document.save(pdf_path)
            document.close()

            store = FilesystemAuditStore(storage_dir)
            report = ValidationReport(
                report_id="a" * 32,
                request_id="req-drawing-assets",
                ifc_path=storage_dir / "model.ifc",
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
                drawing_assets=(
                    DrawingAsset(
                        asset_id="drawing-001",
                        sheet_id="A-101",
                        media_type="application/pdf",
                        source_path=pdf_path,
                    ),
                ),
            )

            store.save(report)
            persisted = store.get(report.report_id)

            self.assertIsNotNone(persisted)
            assert persisted is not None
            self.assertEqual(len(persisted.drawing_assets), 1)
            asset = persisted.drawing_assets[0]
            self.assertEqual(asset.sheet_id, "A-101")
            self.assertEqual(asset.page_number, 1)
            self.assertEqual(asset.media_type, "image/png")
            self.assertGreater(asset.coordinate_width or 0, 0)
            self.assertGreater(asset.coordinate_height or 0, 0)
            self.assertIsNone(asset.source_path)
            self.assertIsNotNone(asset.stored_filename)
            preview_path = (
                storage_dir / "drawing-assets" / report.report_id / str(asset.stored_filename)
            )
            self.assertTrue(preview_path.exists())

    def test_save_materializes_raster_preview_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            image_path = storage_dir / "source-sheet.png"

            pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 120, 60), False)
            pix.set_rect(pix.irect, (255, 255, 255))
            pix.save(image_path)

            store = FilesystemAuditStore(storage_dir)
            report = ValidationReport(
                report_id="b" * 32,
                request_id="req-raster-assets",
                ifc_path=storage_dir / "model.ifc",
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
                drawing_assets=(
                    DrawingAsset(
                        asset_id="drawing-002",
                        sheet_id="A-201",
                        page_number=1,
                        media_type="image/png",
                        source_path=image_path,
                    ),
                ),
            )

            store.save(report)
            persisted = store.get(report.report_id)

            self.assertIsNotNone(persisted)
            assert persisted is not None
            self.assertEqual(len(persisted.drawing_assets), 1)
            asset = persisted.drawing_assets[0]
            self.assertEqual(asset.sheet_id, "A-201")
            self.assertEqual(asset.page_number, 1)
            self.assertEqual(asset.media_type, "image/png")
            self.assertEqual(asset.coordinate_width, 120)
            self.assertEqual(asset.coordinate_height, 60)
            self.assertIsNotNone(asset.stored_filename)
            preview_path = (
                storage_dir / "drawing-assets" / report.report_id / str(asset.stored_filename)
            )
            self.assertTrue(preview_path.exists())
