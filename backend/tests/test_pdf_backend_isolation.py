"""LIC-001 Phase 1: PDF backend selection seam."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.application.services.extraction_integrity_probe import probe_extraction_integrity
from aerobim.domain.models import CapabilityState, DrawingSource
from aerobim.domain.pdf_backend import resolve_pdf_backend
from aerobim.infrastructure.adapters.disabled_pdf_extraction_integrity_producer import (
    DisabledPdfExtractionIntegrityProducer,
)


class PdfBackendIsolationTests(unittest.TestCase):
    def test_resolve_pdf_backend(self) -> None:
        self.assertEqual(resolve_pdf_backend(None), "pdfium")
        self.assertEqual(resolve_pdf_backend("pdfium"), "pdfium")
        self.assertEqual(resolve_pdf_backend("pymupdf"), "pymupdf")
        self.assertEqual(resolve_pdf_backend("none"), "none")
        self.assertEqual(resolve_pdf_backend("OFF"), "none")

    def test_disabled_producer_does_not_import_pymupdf(self) -> None:
        status = probe_extraction_integrity(
            DisabledPdfExtractionIntegrityProducer(),
            (DrawingSource(path=Path("sheet.pdf"), format="pdf"),),
        )
        self.assertEqual(status.status, CapabilityState.NOT_VERIFIED)


if __name__ == "__main__":
    unittest.main()
