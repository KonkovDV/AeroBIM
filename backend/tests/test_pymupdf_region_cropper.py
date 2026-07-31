"""PyMuPDFRegionCropper — optional AGPL path tests (requires pdf-agpl extra)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper

pymupdf = pytest.importorskip("pymupdf")


def _make_pdf(path: Path, *, width: int = 600, height: int = 400) -> None:
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
            data, _ = cropper.crop(_source(tmp), bbox_xyxy=(0.08, 0.12, 0.33, 0.38))
        self.assertTrue(data.startswith(b"\x89PNG"))

    def test_empty_bbox_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cropper = PyMuPDFRegionCropper()
            with self.assertRaises(ValueError):
                cropper.crop(_source(tmp), bbox_xyxy=(10.0, 10.0, 10.0, 10.0))

    def test_missing_path_raises(self) -> None:
        cropper = PyMuPDFRegionCropper()
        with self.assertRaises(ValueError):
            cropper.crop(DrawingSource(path=None, format="pdf"), bbox_xyxy=(0, 0, 1, 1))

    def test_max_side_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = _source(tmp)
            big, _ = PyMuPDFRegionCropper(dpi=200, max_side_px=4096).crop(
                src, bbox_xyxy=(50.0, 50.0, 200.0, 150.0)
            )
            small, _ = PyMuPDFRegionCropper(dpi=200, max_side_px=64).crop(
                src, bbox_xyxy=(50.0, 50.0, 200.0, 150.0)
            )
        self.assertGreater(len(big), len(small))


if __name__ == "__main__":
    unittest.main()
