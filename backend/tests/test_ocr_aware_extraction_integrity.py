"""OCR-aware extraction-integrity enrichment tests (engineering signal only)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdf_fixtures import write_text_pdf

from aerobim.application.services.extraction_integrity_probe import probe_extraction_integrity
from aerobim.domain.extraction_integrity import (
    ExtractionIntegritySignals,
    assess_extraction_integrity,
)
from aerobim.domain.models import CapabilityState, DrawingSource
from aerobim.infrastructure.adapters.ocr_aware_extraction_integrity_producer import (
    OcrAwareExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.pdfminer_extraction_integrity_producer import (
    PdfMinerExtractionIntegrityProducer,
)


class _FakeOcrResult:
    def __init__(self, text: str) -> None:
        self.txts = (text,)
        self.boxes = []
        self.scores = (1.0,)


class _FakeOcrEngine:
    def __init__(self, text: str) -> None:
        self._text = text

    def __call__(self, _path: Path) -> _FakeOcrResult:
        return _FakeOcrResult(self._text)


class OcrAwareExtractionIntegrityTests(unittest.TestCase):
    def test_without_ocr_engine_leaves_ocr_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_text_pdf(Path(tmp) / "t.pdf", "WALL-01 thickness 200 mm")

            class _NoOcr(OcrAwareExtractionIntegrityProducer):
                def _resolve_ocr_engine(self):  # type: ignore[no-untyped-def]
                    return None

            signals = _NoOcr().produce(pdf)
            self.assertIsNone(signals.ocr_char_count)
            self.assertGreater(signals.extracted_char_count or 0, 0)

    def test_ocr_disagreement_warns_in_assessor(self) -> None:
        # Domain path: low extracted/OCR ratio → WARNING (not product claim).
        result = assess_extraction_integrity(
            ExtractionIntegritySignals(
                extracted_char_count=10,
                ocr_char_count=100,
                rendered_text_present=True,
                hidden_text_char_count=0,
                offpage_text_char_count=0,
            )
        )
        self.assertEqual(result.status.value, "warning")
        self.assertTrue(
            any("OCR" in reason or "ocr" in reason.lower() for reason in result.reasons)
        )

    def test_fake_ocr_digit_spoof_fails_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Text layer embeds 3300; OCR of render reports 3000 (same length).
            pdf = write_text_pdf(Path(tmp) / "spoof.pdf", "FireRating 3300")
            producer = OcrAwareExtractionIntegrityProducer(
                text_producer=PdfMinerExtractionIntegrityProducer(),
                ocr_engine_factory=lambda: _FakeOcrEngine("FireRating 3000"),
            )
            status = probe_extraction_integrity(
                producer,
                (DrawingSource(path=pdf, format="pdf"),),
            )
            self.assertEqual(status.status, CapabilityState.FAILED)
            signals = producer.produce(pdf)
            self.assertEqual(signals.extracted_digit_runs, ("3300",))
            self.assertEqual(signals.ocr_digit_runs, ("3000",))

    def test_fake_ocr_enriches_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_text_pdf(Path(tmp) / "t.pdf", "WALL-01 thickness 200 mm")
            producer = OcrAwareExtractionIntegrityProducer(
                text_producer=PdfMinerExtractionIntegrityProducer(),
                ocr_engine_factory=lambda: _FakeOcrEngine("WALL-01 thickness 200 mm EXTRA"),
            )
            status = probe_extraction_integrity(
                producer,
                (DrawingSource(path=pdf, format="pdf"),),
            )
            # Agreement enough for OK / not_verified — must not invent FAILED.
            self.assertIn(status.status, {CapabilityState.OK, CapabilityState.NOT_VERIFIED})
            signals = producer.produce(pdf)
            self.assertIsNotNone(signals.ocr_char_count)
            self.assertGreater(signals.ocr_char_count or 0, 0)
            self.assertEqual(signals.extracted_digit_runs, ("200",))
            self.assertEqual(signals.ocr_digit_runs, ("200",))


if __name__ == "__main__":
    unittest.main()
