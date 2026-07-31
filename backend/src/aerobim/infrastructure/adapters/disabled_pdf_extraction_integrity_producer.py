"""Fail-closed extraction-integrity producer when PDF backend is disabled (LIC-001 Phase 1)."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.extraction_integrity import ExtractionIntegritySignals


class DisabledPdfExtractionIntegrityProducer:
    """Used when ``pdf_backend=none`` — does not import PyMuPDF."""

    def produce(self, path: Path) -> ExtractionIntegritySignals:
        _ = path
        # No signals → assessor yields REVIEW_REQUIRED → capability NOT_VERIFIED.
        return ExtractionIntegritySignals()


__all__ = ["DisabledPdfExtractionIntegrityProducer"]
