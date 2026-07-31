"""PdfiumRegionCropper — region crop tests (permissive PDFium path, LIC-001 Option B)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdf_fixtures import write_box_pdf

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.pdfium_region_cropper import PdfiumRegionCropper


class PdfiumRegionCropperTests(unittest.TestCase):
    def test_crops_page_point_bbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            cropper = PdfiumRegionCropper(dpi=72)
            payload, media = cropper.crop(
                DrawingSource(path=pdf, format="pdf"),
                bbox_xyxy=(50, 50, 200, 150),
            )
            self.assertEqual(media, "image/png")
            self.assertGreater(len(payload), 32)
            self.assertTrue(payload.startswith(b"\x89PNG"))

    def test_normalized_coordinates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            cropper = PdfiumRegionCropper(dpi=72, coordinate_system="normalized-0-1")
            payload, _ = cropper.crop(
                DrawingSource(path=pdf, format="pdf"),
                bbox_xyxy=(0.05, 0.05, 0.4, 0.3),
            )
            self.assertTrue(payload.startswith(b"\x89PNG"))

    def test_degenerate_bbox_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            cropper = PdfiumRegionCropper()
            with self.assertRaises(ValueError):
                cropper.crop(
                    DrawingSource(path=pdf, format="pdf"),
                    bbox_xyxy=(10, 10, 10, 10),
                )

    def test_missing_path_fails_closed(self) -> None:
        cropper = PdfiumRegionCropper()
        with self.assertRaises(ValueError):
            cropper.crop(DrawingSource(path=None, format="pdf"), bbox_xyxy=(0, 0, 1, 1))

    def test_max_side_budget_reduces_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            big, _ = PdfiumRegionCropper(dpi=200, max_side_px=4096).crop(
                DrawingSource(path=pdf, format="pdf"),
                bbox_xyxy=(50, 50, 200, 150),
            )
            small, _ = PdfiumRegionCropper(dpi=200, max_side_px=64).crop(
                DrawingSource(path=pdf, format="pdf"),
                bbox_xyxy=(50, 50, 200, 150),
            )
            self.assertGreater(len(big), len(small))


if __name__ == "__main__":
    unittest.main()
