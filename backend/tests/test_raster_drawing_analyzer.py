from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdf_fixtures import write_text_pdf

from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer


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


class RasterDrawingAnalyzerTests(unittest.TestCase):
    def test_pdf_blocks_are_converted_into_drawing_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")

            analyzer = RasterDrawingAnalyzer()
            annotations = analyzer.analyze_image(pdf_path, sheet_id="A-101")

            self.assertEqual(len(annotations), 1)
            annotation = annotations[0]
            self.assertEqual(annotation.sheet_id, "A-101")
            self.assertEqual(annotation.target_ref, "WALL-01")
            self.assertEqual(annotation.measure_name, "thickness")
            self.assertEqual(annotation.observed_value, "250")
            self.assertEqual(annotation.unit, "mm")
            self.assertEqual(annotation.source, "raster-drawing-analyzer")
            self.assertIsNotNone(annotation.problem_zone)
            self.assertEqual(annotation.problem_zone.page_number, 1)
            self.assertGreater(annotation.problem_zone.width, 0)
            self.assertGreater(annotation.problem_zone.height, 0)

    def test_raster_ocr_result_is_converted_into_drawing_annotations(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")
            image_path = Path(tmp.name)

        try:
            analyzer = RasterDrawingAnalyzer(ocr_engine_factory=_FakeOcrEngine)
            annotations = analyzer.analyze_image(image_path, sheet_id="A-201")

            self.assertEqual(len(annotations), 1)
            annotation = annotations[0]
            self.assertEqual(annotation.sheet_id, "A-201")
            self.assertEqual(annotation.target_ref, "WALL-IMG-01")
            self.assertEqual(annotation.measure_name, "thickness")
            self.assertEqual(annotation.observed_value, "220")
            self.assertEqual(annotation.unit, "mm")
            self.assertEqual(annotation.source, "raster-drawing-analyzer-ocr")
            self.assertEqual(annotation.problem_zone.page_number, 1)
            self.assertEqual(annotation.problem_zone.x, 10)
            self.assertEqual(annotation.problem_zone.y, 20)
            self.assertEqual(annotation.problem_zone.width, 100)
            self.assertEqual(annotation.problem_zone.height, 40)
        finally:
            image_path.unlink(missing_ok=True)

    def test_numpy_ocr_boxes_do_not_crash_truth_test(self) -> None:
        """RapidOCR returns ndarray boxes; `x or []` must not be used (SFC-A68)."""
        try:
            import numpy as np
        except ModuleNotFoundError:
            self.skipTest("numpy not installed")

        class _NumpyOcrResult:
            def __init__(self) -> None:
                self.boxes = np.array(
                    [[[10.0, 20.0], [110.0, 20.0], [110.0, 60.0], [10.0, 60.0]]],
                    dtype=np.float32,
                )
                self.txts = ("WALL-NP-01 thickness 180 mm",)
                self.scores = (0.95,)

        class _NumpyOcrEngine:
            def __call__(self, _image_path: object) -> _NumpyOcrResult:
                return _NumpyOcrResult()

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\n")
            image_path = Path(tmp.name)
        try:
            analyzer = RasterDrawingAnalyzer(ocr_engine_factory=_NumpyOcrEngine)
            annotations = analyzer.analyze_image(image_path, sheet_id="NP-1")
            self.assertEqual(len(annotations), 1)
            self.assertEqual(annotations[0].target_ref, "WALL-NP-01")
            self.assertEqual(annotations[0].observed_value, "180")
        finally:
            image_path.unlink(missing_ok=True)

    def test_committed_vector_pdf_fixture(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "drawings"
            / "wall-thickness-vector.pdf"
        )
        if not path.is_file():
            self.skipTest("committed vector PDF fixture missing")
        annotations = RasterDrawingAnalyzer().analyze_image(path, sheet_id="A-101")
        self.assertGreaterEqual(len(annotations), 1)
        annotation = annotations[0]
        self.assertEqual(annotation.target_ref, "WALL-01")
        self.assertEqual(annotation.measure_name, "thickness")
        self.assertEqual(annotation.observed_value, "250")
        self.assertEqual(annotation.unit, "mm")

    def test_committed_scan_png_with_fake_ocr(self) -> None:
        path = (
            Path(__file__).resolve().parents[2] / "samples" / "drawings" / "wall-thickness-scan.png"
        )
        if not path.is_file():
            self.skipTest("committed scan PNG fixture missing")
        annotations = RasterDrawingAnalyzer(ocr_engine_factory=_FakeOcrEngine).analyze_image(
            path, sheet_id="A-201"
        )
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].target_ref, "WALL-IMG-01")
        self.assertEqual(annotations[0].observed_value, "220")

    def test_committed_scan_png_with_rapidocr_when_installed(self) -> None:
        import importlib.util

        if importlib.util.find_spec("rapidocr") is None:
            self.skipTest("rapidocr optional extra not installed")
        path = (
            Path(__file__).resolve().parents[2] / "samples" / "drawings" / "wall-thickness-scan.png"
        )
        if not path.is_file():
            self.skipTest("committed scan PNG fixture missing")
        annotations = RasterDrawingAnalyzer().analyze_image(path, sheet_id="A-201")
        texts = " ".join(f"{a.target_ref} {a.observed_value}" for a in annotations)
        self.assertTrue(
            any(a.observed_value == "220" for a in annotations),
            f"RapidOCR did not recover 220 mm from fixture: {texts!r}",
        )


if __name__ == "__main__":
    unittest.main()
