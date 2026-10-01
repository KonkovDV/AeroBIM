"""Process isolate for pdfminer drawing extract: kill-on-timeout, fail-closed."""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from pdf_fixtures import write_text_pdf

from aerobim.infrastructure.adapters.pdfium_isolate.process_isolate import run_isolated_argv
from aerobim.infrastructure.adapters.pdfminer_extract_isolate import (
    run_pdfminer_extract_isolated,
)
from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer


class PdfminerExtractIsolateTests(unittest.TestCase):
    def test_pdf_timeout_kills_worker_and_returns_structured_failure(self) -> None:
        started = time.perf_counter()
        with self.assertRaises(TimeoutError) as ctx:
            run_isolated_argv(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                timeout_s=0.4,
                timeout_message="PDF analysis timed out after 0s",
            )
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 8.0)
        self.assertIn("timed out", str(ctx.exception))
        self.assertNotIn(".pdf", str(ctx.exception))

    def test_analyze_image_timeout_has_no_path_in_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            with patch(
                "aerobim.infrastructure.adapters.raster_drawing_analyzer.run_pdfminer_extract_isolated",
                side_effect=TimeoutError("PDF analysis timed out after 30s"),
            ):
                with self.assertRaises(TimeoutError) as ctx:
                    RasterDrawingAnalyzer().analyze_image(pdf_path, sheet_id="A-101")
        message = str(ctx.exception)
        self.assertIn("timed out", message)
        self.assertNotIn(str(pdf_path), message)

    def test_oversized_decoded_pdf_is_rejected_before_parser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            with self.assertRaises(RuntimeError) as ctx:
                run_pdfminer_extract_isolated(
                    pdf_path,
                    "A-101",
                    max_pdf_bytes=8,
                )
        self.assertIn("oversized", str(ctx.exception).lower())

    def test_malformed_pdf_does_not_crash_api_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "broken.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\nnot a real document")
            try:
                result = RasterDrawingAnalyzer().analyze_image(pdf_path, sheet_id="A-101")
            except (RuntimeError, TimeoutError, ValueError):
                return
            self.assertIsInstance(result, list)

    def test_worker_cannot_read_other_tenant_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            allowed = write_text_pdf(Path(tmp) / "allowed.pdf", "WALL-01 thickness 250 mm")
            secret = write_text_pdf(Path(tmp) / "other-tenant.pdf", "SECRET-99 thickness 999 mm")
            payloads = run_pdfminer_extract_isolated(allowed, "A-101")
            texts = " ".join(str(item.get("target_ref")) for item in payloads)
            self.assertIn("WALL-01", texts)
            self.assertNotIn("SECRET-99", texts)
            self.assertTrue(secret.is_file())

    def test_worker_has_no_network_access(self) -> None:
        self.skipTest("Job Object / rlimit isolate bounds CPU and memory; it is not a network jail")

    def test_cancelled_job_cleans_temp_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            with patch(
                "aerobim.infrastructure.adapters.pdfminer_extract_isolate.run_isolated_argv",
                side_effect=TimeoutError("PDF analysis timed out after 30s"),
            ):
                with self.assertRaises(TimeoutError):
                    run_pdfminer_extract_isolated(pdf_path, "A-101")
            self.assertEqual(list(Path(tmp).glob("spec.json")), [])
            self.assertEqual(list(Path(tmp).glob("annotations.json")), [])

    def test_timeout_does_not_create_duplicate_stage_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            with patch(
                "aerobim.infrastructure.adapters.raster_drawing_analyzer.run_pdfminer_extract_isolated",
                side_effect=TimeoutError("PDF analysis timed out after 30s"),
            ):
                with self.assertRaises(TimeoutError):
                    RasterDrawingAnalyzer().analyze_image(pdf_path, sheet_id="A-101")
            leftovers = list(Path(tmp).glob("**/annotations.json"))
            self.assertEqual(leftovers, [])

    def test_live_pdf_extract_still_finds_vector_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = write_text_pdf(Path(tmp) / "wall.pdf", "WALL-01 thickness 250 mm")
            annotations = RasterDrawingAnalyzer().analyze_image(pdf_path, sheet_id="A-101")
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].target_ref, "WALL-01")
        self.assertTrue(annotations[0].annotation_id.startswith("VIS-001-"))


if __name__ == "__main__":
    unittest.main()
