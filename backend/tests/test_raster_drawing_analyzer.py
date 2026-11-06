from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pdf_fixtures import _wrap_single_page, write_text_pdf

from aerobim.domain.pdf_page_frame import (
    media_box_from_viewed_size,
    upright_char_box,
    upright_page_size,
)
from aerobim.domain.simple_text_pdf import write_simple_text_pdf
from aerobim.domain.stamp_caption_above import PlacedLine, line_center_in_title_block
from aerobim.infrastructure.adapters.raster_drawing_analyzer import (
    RasterDrawingAnalyzer,
    _char_continues_line,
    _extend_line_band,
    _pdfium_text_lines,
    _TextRegion,
)


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

    def test_pdfium_failure_falls_back_to_pdfminer_inside_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            analyzer = RasterDrawingAnalyzer()
            with patch.object(analyzer, "_extract_pdf_pdfium", side_effect=OSError("pdfium")):
                annotations = analyzer.extract_pdf_in_process(pdf_path, "A-101")
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].target_ref, "WALL-01")

    def test_hyphen_on_its_own_baseline_stays_on_the_measure_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_simple_text_pdf(
                Path(tmp) / "wall.pdf",
                "A-101  WALL-01 thickness 150 mm",
            )
            annotations = RasterDrawingAnalyzer().extract_pdf_in_process(pdf_path, "A-101")
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].target_ref, "WALL-01")
        self.assertEqual(annotations[0].observed_value, "150")
        self.assertEqual(annotations[0].unit, "mm")

    def test_a_paired_size_is_not_one_thickness(self) -> None:
        region = _TextRegion(
            text="OPEN-01 width 500 mm x 300 mm",
            page_number=1,
            x=10,
            y=10,
            width=80,
            height=12,
        )
        annotations = RasterDrawingAnalyzer()._extract_annotations_from_region(region, "A-101")
        self.assertEqual(annotations, [])

    def test_a_thickness_beside_a_paired_size_is_kept(self) -> None:
        region = _TextRegion(
            text="WALL-01 thickness 250 mm opening 500×300",
            page_number=1,
            x=10,
            y=10,
            width=80,
            height=12,
        )
        annotations = RasterDrawingAnalyzer()._extract_annotations_from_region(region, "A-101")
        self.assertEqual(
            [(item.measure_name, item.observed_value) for item in annotations],
            [("thickness", "250")],
        )
        same_side = _TextRegion(
            text="WALL-01 thickness 500.0 mm opening 500x300",
            page_number=1,
            x=10,
            y=10,
            width=80,
            height=12,
        )
        self.assertEqual(
            RasterDrawingAnalyzer()._extract_annotations_from_region(same_side, "A-101"),
            [],
        )
        word = _TextRegion(
            text="WALL-01 thickness 2 mm, max 3 mm",
            page_number=1,
            x=10,
            y=10,
            width=80,
            height=12,
        )
        kept = RasterDrawingAnalyzer()._extract_annotations_from_region(word, "A-101")
        self.assertEqual(
            [(item.measure_name, item.observed_value) for item in kept], [("thickness", "2")]
        )

    def test_stamp_pairs_stay_in_the_title_block(self) -> None:
        page_w, page_h = 612.0, 792.0
        analyzer = RasterDrawingAnalyzer()
        body = [
            PlacedLine("Шифр", 40.0, 40.0, 40.0, 10.0),
            PlacedLine("АР-1", 40.0, 52.0, 40.0, 10.0),
        ]
        self.assertEqual(
            analyzer._stamp_annotations(
                body,
                sheet_id="A-101",
                page_number=1,
                page_width=page_w,
                page_height=page_h,
            ),
            [],
        )
        corner = [
            PlacedLine("Шифр", page_w - 120.0, page_h - 50.0, 40.0, 10.0),
            PlacedLine("АР-1", page_w - 120.0, page_h - 36.0, 40.0, 10.0),
        ]
        kept = analyzer._stamp_annotations(
            corner,
            sheet_id="A-101",
            page_number=1,
            page_width=page_w,
            page_height=page_h,
        )
        self.assertEqual([item.observed_value for item in kept], ["АР-1"])
        standard = [
            PlacedLine("Шифр", page_w - 120.0, page_h - 50.0, 40.0, 10.0),
            PlacedLine("ГОСТ 21.101", page_w - 120.0, page_h - 36.0, 80.0, 10.0),
        ]
        self.assertEqual(
            analyzer._stamp_annotations(
                standard,
                sheet_id="A-101",
                page_number=1,
                page_width=page_w,
                page_height=page_h,
            ),
            [],
        )

    def test_a_rotated_sheet_is_read_upright(self) -> None:
        box = upright_char_box(
            10.0,
            10.0,
            20.0,
            20.0,
            rotation=90,
            media_x0=0.0,
            media_y0=0.0,
            media_x1=595.0,
            media_y1=842.0,
        )
        self.assertEqual(box, (10.0, 575.0, 20.0, 585.0))
        self.assertEqual(upright_page_size(90, 0.0, 0.0, 595.0, 842.0), (842.0, 595.0))
        self.assertEqual(media_box_from_viewed_size(90, 400.0, 200.0), (0.0, 0.0, 200.0, 400.0))
        self.assertEqual(
            upright_char_box(
                15.0,
                25.0,
                16.0,
                26.0,
                rotation=0,
                media_x0=10.0,
                media_y0=20.0,
                media_x1=100.0,
                media_y1=200.0,
            ),
            (5.0, 5.0, 6.0, 6.0),
        )
        turned = upright_char_box(
            580.0,
            820.0,
            590.0,
            830.0,
            rotation=90,
            media_x0=0.0,
            media_y0=0.0,
            media_x1=595.0,
            media_y1=842.0,
        )
        page_w, page_h = upright_page_size(90, 0.0, 0.0, 595.0, 842.0)
        line = PlacedLine(
            "Шифр",
            x=turned[0],
            y=page_h - turned[3],
            width=turned[2] - turned[0],
            height=turned[3] - turned[1],
        )
        self.assertTrue(line_center_in_title_block(line, page_width=page_w, page_height=page_h))
        stored = PlacedLine("Шифр", x=box[0], y=page_h - box[3], width=10.0, height=10.0)
        self.assertFalse(line_center_in_title_block(stored, page_width=page_w, page_height=page_h))

    def test_pdfium_turns_a_rotated_page_before_the_line(self) -> None:
        import pypdfium2 as pdfium

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "turned.pdf"
            content = b"BT /F1 12 Tf 10 10 Td (STAMP) Tj ET\n"
            pdf_path.write_bytes(
                _wrap_single_page(content, page_w=200, page_h=400, with_font=True, rotate=90)
            )
            document = pdfium.PdfDocument(str(pdf_path))
            try:
                page = document[0]
                textpage = page.get_textpage()
                try:
                    media = page.get_mediabox()
                    lines = _pdfium_text_lines(
                        textpage,
                        rotation=int(page.get_rotation()),
                        media_box=tuple(float(value) for value in media),
                    )
                finally:
                    textpage.close()
                    page.close()
            finally:
                document.close()
        self.assertEqual("".join(line[0] for line in lines), "STAMP")
        self.assertTrue(all(line[2] < 80.0 for line in lines))

    def test_hyphen_box_overlaps_the_letter_band(self) -> None:
        self.assertTrue(_char_continues_line(723.01, 724.24, 720.0, 730.02))
        self.assertFalse(_char_continues_line(400.0, 410.0, 720.0, 730.0))

    def test_a_tall_overlap_does_not_swallow_the_next_line(self) -> None:
        bottom, top = _extend_line_band(720.0, 730.0, 0.0, 800.0)
        self.assertEqual((bottom, top), (719.0, 731.0))
        self.assertFalse(_char_continues_line(700.0, 710.0, bottom, top))

    def test_two_baselines_stay_two_measures(self) -> None:
        content = (
            b"BT /F1 12 Tf 72 720 Td (WALL-01 thickness 250 mm) Tj ET\n"
            b"BT /F1 12 Tf 72 400 Td (BEAM-02 thickness 100 mm) Tj ET\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "two.pdf"
            pdf_path.write_bytes(_wrap_single_page(content, page_w=612, page_h=792, with_font=True))
            annotations = RasterDrawingAnalyzer().extract_pdf_in_process(pdf_path, "A-101")
        by_target = {item.target_ref: item for item in annotations}
        self.assertEqual(set(by_target), {"WALL-01", "BEAM-02"})
        wall_zone = by_target["WALL-01"].problem_zone
        beam_zone = by_target["BEAM-02"].problem_zone
        self.assertIsNotNone(wall_zone)
        self.assertIsNotNone(beam_zone)
        assert wall_zone is not None and beam_zone is not None
        self.assertGreater(abs((wall_zone.y or 0.0) - (beam_zone.y or 0.0)), 100.0)

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
        try:
            annotations = RasterDrawingAnalyzer().analyze_image(path, sheet_id="A-201")
        except (ImportError, OSError) as exc:
            self.skipTest(f"rapidocr extra present but engine import failed: {exc}")
        texts = " ".join(f"{a.target_ref} {a.observed_value}" for a in annotations)
        self.assertTrue(
            any(a.observed_value == "220" for a in annotations),
            f"RapidOCR did not recover 220 mm from fixture: {texts!r}",
        )

    def test_same_annotation_different_bbox_keeps_two_evidence_locations(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        annotations = []
        for index in range(20):
            region = _TextRegion(
                text="WALL-01 thickness 250 mm",
                page_number=1,
                x=10.0 + index * 15.0,
                y=20.0,
                width=100.0,
                height=40.0,
            )
            annotations.extend(analyzer._extract_annotations_from_region(region, "A-101"))
        kept = analyzer._deduplicate_annotations(annotations)
        self.assertEqual(len(kept), 20)
        ids = {item.annotation_id for item in kept}
        self.assertEqual(len(ids), 20)

    def test_same_annotation_same_bbox_is_deduplicated(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        region = _TextRegion(
            text="WALL-01 thickness 250 mm",
            page_number=1,
            x=10.0,
            y=20.0,
            width=100.0,
            height=40.0,
        )
        first = analyzer._extract_annotations_from_region(region, "A-101")
        second = analyzer._extract_annotations_from_region(region, "A-101")
        kept = analyzer._deduplicate_annotations([*first, *second])
        self.assertEqual(len(kept), 1)

    def test_stamp_and_explication_same_text_keep_two_locations(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        stamp = _TextRegion(
            text="WALL-01 thickness 250 mm",
            page_number=1,
            x=40.0,
            y=20.0,
            width=80.0,
            height=12.0,
        )
        explication = _TextRegion(
            text="WALL-01 thickness 250 mm",
            page_number=1,
            x=40.0,
            y=400.0,
            width=180.0,
            height=20.0,
        )
        kept = analyzer._deduplicate_annotations(
            [
                *analyzer._extract_annotations_from_region(stamp, "A-101"),
                *analyzer._extract_annotations_from_region(explication, "A-101"),
            ]
        )
        self.assertEqual(len(kept), 2)

    def test_negative_and_large_coords_stay_distinct(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        negative = _TextRegion(
            text="WALL-01 thickness 250 mm",
            page_number=1,
            x=-50.0,
            y=-10.0,
            width=100.0,
            height=40.0,
        )
        large = _TextRegion(
            text="WALL-01 thickness 250 mm",
            page_number=1,
            x=1_000_000.0,
            y=20.0,
            width=100.0,
            height=40.0,
        )
        kept = analyzer._deduplicate_annotations(
            [
                *analyzer._extract_annotations_from_region(negative, "A-101"),
                *analyzer._extract_annotations_from_region(large, "A-101"),
            ]
        )
        self.assertEqual(len(kept), 2)

    def test_an_execution_token_is_a_measure(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        region = _TextRegion(
            text="ITEM-A исполнение T",
            page_number=1,
            x=10.0,
            y=20.0,
            width=80.0,
            height=12.0,
        )
        annotation = analyzer._parse_regex_line("ITEM-A исполнение T", "A-101", region)
        self.assertIsNotNone(annotation)
        assert annotation is not None
        self.assertEqual(annotation.measure_name, "execution")
        self.assertEqual(annotation.observed_value, "T")
        self.assertEqual(annotation.target_ref, "ITEM-A")
        self.assertIsNone(analyzer._parse_regex_line("ITEM-A исполнение таблицы", "A-101", region))

    def test_a_piece_count_is_one_count(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        region = _TextRegion(
            text="ITEM-A 28 шт",
            page_number=1,
            x=10.0,
            y=20.0,
            width=80.0,
            height=12.0,
        )
        pieces = analyzer._parse_regex_line("ITEM-A 28 шт", "A-101", region)
        english = analyzer._parse_regex_line("ITEM-A 27 pcs", "A-102", region)
        self.assertIsNotNone(pieces)
        self.assertIsNotNone(english)
        assert pieces is not None and english is not None
        self.assertEqual(pieces.measure_name, "count")
        self.assertEqual(pieces.observed_value, "28")
        self.assertEqual(pieces.unit, "шт")
        self.assertEqual(english.unit, "шт")
        self.assertEqual(english.observed_value, "27")
        thickness = analyzer._parse_regex_line("WALL-01 thickness 250 mm", "A-101", region)
        self.assertIsNotNone(thickness)
        assert thickness is not None
        self.assertEqual(thickness.measure_name, "thickness")

    def test_a_detail_citation_is_not_a_count(self) -> None:
        analyzer = RasterDrawingAnalyzer()
        region = _TextRegion(
            text="см. узел 1",
            page_number=1,
            x=10.0,
            y=20.0,
            width=80.0,
            height=12.0,
        )
        found = analyzer._extract_annotations_from_region(region, "A-101")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].source, "detail-callout")
        self.assertEqual(found[0].observed_value, "1")


if __name__ == "__main__":
    unittest.main()
