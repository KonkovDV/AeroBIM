from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pymupdf

from aerobim.infrastructure.adapters.vlm_drawing_analyzer import VlmDrawingAnalyzer


class _FakeOcrResult:
    def __init__(self) -> None:
        self.boxes = [
            [[10, 20], [110, 20], [110, 60], [10, 60]],
        ]
        self.txts = ("WALL-IMG-01 thickness 220 mm",)
        self.scores = (0.99,)


class _FakeOcrEngine:
    def __call__(self, _image_path: Path) -> _FakeOcrResult:
        return _FakeOcrResult()


class VlmDrawingAnalyzerTests(unittest.TestCase):
    def test_pdf_blocks_are_converted_into_drawing_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = Path(tmp.name)

        try:
            document = pymupdf.open()
            page = document.new_page()
            page.insert_text((72, 72), "WALL-01 thickness 250 mm")
            document.save(pdf_path)
            document.close()

            analyzer = VlmDrawingAnalyzer()
            annotations = analyzer.analyze_image(pdf_path, sheet_id="A-101")

            self.assertEqual(len(annotations), 1)
            annotation = annotations[0]
            self.assertEqual(annotation.sheet_id, "A-101")
            self.assertEqual(annotation.target_ref, "WALL-01")
            self.assertEqual(annotation.measure_name, "thickness")
            self.assertEqual(annotation.observed_value, "250")
            self.assertEqual(annotation.unit, "mm")
            self.assertEqual(annotation.source, "vision-analyzer")
            self.assertIsNotNone(annotation.problem_zone)
            self.assertEqual(annotation.problem_zone.page_number, 1)
            self.assertGreater(annotation.problem_zone.width, 0)
            self.assertGreater(annotation.problem_zone.height, 0)
        finally:
            pdf_path.unlink(missing_ok=True)

    def test_raster_ocr_result_is_converted_into_drawing_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")
            image_path = Path(tmp.name)

        try:
            analyzer = VlmDrawingAnalyzer(ocr_engine_factory=_FakeOcrEngine)
            annotations = analyzer.analyze_image(image_path, sheet_id="A-201")

            self.assertEqual(len(annotations), 1)
            annotation = annotations[0]
            self.assertEqual(annotation.sheet_id, "A-201")
            self.assertEqual(annotation.target_ref, "WALL-IMG-01")
            self.assertEqual(annotation.measure_name, "thickness")
            self.assertEqual(annotation.observed_value, "220")
            self.assertEqual(annotation.unit, "mm")
            self.assertEqual(annotation.problem_zone.page_number, 1)
            self.assertEqual(annotation.problem_zone.x, 10)
            self.assertEqual(annotation.problem_zone.y, 20)
            self.assertEqual(annotation.problem_zone.width, 100)
            self.assertEqual(annotation.problem_zone.height, 40)
        finally:
            image_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
