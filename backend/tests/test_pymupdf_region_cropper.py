"""PyMuPDFRegionCropper — real region crop tests (PyMuPDF is a shipped core dep)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper


def _make_pdf(path: Path, *, width: int = 600, height: int = 400) -> None:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    page.draw_rect(pymupdf.Rect(50, 50, 200, 150), fill=(0, 0, 0))
    page.insert_text((60, 200), "AR-01 Ст-1")
    doc.save(str(path))
    doc.close()


def _source(tmp: str, name: str = "sheet.pdf") -> DrawingSource:
    path = Path(tmp) / name
    _make_pdf(path)
    return DrawingSource(path=path, sheet_id="AR-01")


class PyMuPDFRegionCropperTests(unittest.TestCase):
    def test_crop_returns_png_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cropper = PyMuPDFRegionCropper(dpi=72)
            data, media_type = cropper.crop(_source(tmp), bbox_xyxy=(50.0, 50.0, 200.0, 150.0))
        self.assertEqual(media_type, "image/png")
        self.assertTrue(data.startswith(b"\x89PNG"))
        self.assertGreater(len(data), 100)

    def test_normalized_coordinate_system(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cropper = PyMuPDFRegionCropper(dpi=72, coordinate_system="normalized-0-1")
            data, _ = cropper.crop(_source(tmp), bbox_xyxy=(0.0, 0.0, 0.5, 0.5))
        self.assertTrue(data.startswith(b"\x89PNG"))

    def test_degenerate_rect_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cropper = PyMuPDFRegionCropper()
            with self.assertRaises(ValueError):
                cropper.crop(_source(tmp), bbox_xyxy=(50.0, 50.0, 50.0, 150.0))

    def test_out_of_bounds_rect_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cropper = PyMuPDFRegionCropper()
            with self.assertRaises(ValueError):
                cropper.crop(_source(tmp), bbox_xyxy=(5000.0, 5000.0, 6000.0, 6000.0))

    def test_no_path_fails_closed(self) -> None:
        cropper = PyMuPDFRegionCropper()
        with self.assertRaises(ValueError):
            cropper.crop(DrawingSource(path=None, sheet_id="X"), bbox_xyxy=(0.0, 0.0, 1.0, 1.0))

    def test_dpi_budget_shrinks_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = _source(tmp)
            big, _ = PyMuPDFRegionCropper(dpi=200, max_side_px=4096).crop(
                source, bbox_xyxy=(0.0, 0.0, 600.0, 400.0)
            )
            small, _ = PyMuPDFRegionCropper(dpi=200, max_side_px=64).crop(
                source, bbox_xyxy=(0.0, 0.0, 600.0, 400.0)
            )
        self.assertLess(len(small), len(big))


if __name__ == "__main__":
    unittest.main()
