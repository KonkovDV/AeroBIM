"""PDF /Rotate probe for PII prior orientation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdf_fixtures import write_box_pdf

from aerobim.infrastructure.adapters.pdf_page_orientation import read_page_rotate_degrees


class PdfPageOrientationTests(unittest.TestCase):
    def test_raster_is_visual_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            self.assertEqual(read_page_rotate_degrees(path), 0)

    def test_pdf_default_rotation_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_box_pdf(Path(tmp) / "box.pdf")
            self.assertEqual(read_page_rotate_degrees(pdf), 0)

    def test_unknown_suffix_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.dwg"
            path.write_bytes(b"not-a-pdf")
            self.assertIsNone(read_page_rotate_degrees(path))


if __name__ == "__main__":
    unittest.main()
