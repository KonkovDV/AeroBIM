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

    def test_page_point_rejects_ambiguous_normalized_bbox(self) -> None:
        """RT-STAMP-09: page-point cropper must not silently accept 0..1 boxes."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            cropper = PdfiumRegionCropper(dpi=72, coordinate_system="page-point")
            with self.assertRaises(ValueError) as ctx:
                cropper.crop(
                    DrawingSource(path=pdf, format="pdf"),
                    bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
                )
            self.assertIn("normalized-0-1", str(ctx.exception))

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

    def test_cropper_module_does_not_import_pypdfium2(self) -> None:
        import inspect

        from aerobim.infrastructure.adapters import pdfium_region_cropper as mod

        source = inspect.getsource(mod)
        self.assertNotIn("import pypdfium2", source)
        self.assertIn("run_pdfium_crop_isolated", source)

    def test_worker_crash_is_runtime_error_not_success(self) -> None:
        from subprocess import CompletedProcess
        from unittest.mock import patch

        from aerobim.infrastructure.adapters.pdfium_process_isolate import (
            run_pdfium_crop_isolated,
        )

        fake = CompletedProcess(args=[], returncode=1, stdout=b"", stderr=b"worker boom")
        with patch(
            "aerobim.infrastructure.adapters.pdfium_process_isolate.subprocess.run",
            return_value=fake,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                run_pdfium_crop_isolated(
                    {
                        "path": "x.pdf",
                        "page_number": 0,
                        "bbox_xyxy": [0, 0, 1, 1],
                        "dpi": 72,
                        "coordinate_system": "page-point",
                        "max_side_px": 64,
                    }
                )
        self.assertIn("exit 1", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
