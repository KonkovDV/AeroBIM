"""Extraction-integrity gate (P-003): extracted text is not automatically evidence.

Red Team A-class risk: a PDF can render one thing while the extraction layer yields
another (hidden/invisible text, white-on-white, zero-size fonts, off-page text,
duplicated layers, OCR overlays). This DOMAIN core assesses integrity SIGNALS supplied
by the ingestion/extraction layer -- it does NOT parse PDFs and is NOT a
render-vs-extract product capability (that needs a renderer adapter behind a port).

Honesty rules (coverage/region-quality lesson):
- "text not extracted" is NEVER "text absent" -- rendered-but-unextracted -> FAILED;
- hidden/invisible text NEVER enters the evidence base unmarked -> REVIEW_REQUIRED;
- no signals -> REVIEW_REQUIRED (never a silent OK);
- non-finite / negative counts are corrupt measurements -> UNKNOWN, never silently good.

Domain-pure, VERDICT-NEUTRAL: does NOT set ``summary.passed`` (ADR-001) -- it gates
whether extracted text may be TRUSTED as evidence, not the engineering verdict.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ExtractionIntegrityStatus(StrEnum):
    OK = "ok"
    """Extraction is consistent with the known signals -- text may be used as evidence."""
    WARNING = "warning"
    """Suspicious but not disqualifying -- text usable only with the warning attached."""
    FAILED = "failed"
    """Extraction contradicts rendering evidence -- extracted text must NOT be trusted."""
    REVIEW_REQUIRED = "review_required"
    """Signals insufficient or hidden-text markers present -- expert required."""


@dataclass(frozen=True)
class ExtractionIntegritySignals:
    """Signals produced by the ingestion/extraction layer for one source/page scope."""

    extracted_char_count: int | None = None
    rendered_text_present: bool | None = None
    """True when rendering evidence shows visible text (e.g. raster crop has glyphs)."""
    ocr_char_count: int | None = None
    hidden_text_char_count: int | None = None
    """Chars from invisible layers: render mode 3, white-on-white, zero-size fonts."""
    offpage_text_char_count: int | None = None
    duplicated_layer_count: int | None = None


@dataclass(frozen=True)
class ExtractionIntegrityThresholds:
    ocr_agreement_ratio: float = 0.5
    """Extracted/OCR char-count ratio below which the layers disagree suspiciously."""


@dataclass(frozen=True)
class ExtractionIntegrityResult:
    status: ExtractionIntegrityStatus
    reasons: tuple[str, ...]

    def trusted_as_evidence(self) -> bool:
        """Only OK text may enter cross-document/LLM paths without escalation."""
        return self.status is ExtractionIntegrityStatus.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "extraction-integrity",
            "note": (
                "gates whether extracted text may be trusted as evidence; "
                "'text not extracted' != 'text absent'; hidden/invisible text never "
                "enters evidence unmarked; verdict-neutral (does NOT set "
                "summary.passed, ADR-001); signal-level core, not a render-vs-extract "
                "product capability"
            ),
            "status": self.status.value,
            "reasons": list(self.reasons),
            "trusted_as_evidence": self.trusted_as_evidence(),
        }


def _count(value: int | None) -> int | None:
    """Normalize corrupt counts: None, negatives, and non-finite floats are UNKNOWN."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        value = int(value)
    return value if value >= 0 else None


def assess_extraction_integrity(
    signals: ExtractionIntegritySignals,
    thresholds: ExtractionIntegrityThresholds | None = None,
) -> ExtractionIntegrityResult:
    """Assess extraction integrity (worst-severity wins; OK needs positive evidence)."""
    t = thresholds if thresholds is not None else ExtractionIntegrityThresholds()
    extracted = _count(signals.extracted_char_count)
    ocr = _count(signals.ocr_char_count)
    hidden = _count(signals.hidden_text_char_count)
    offpage = _count(signals.offpage_text_char_count)
    duplicated = _count(signals.duplicated_layer_count)
    rendered = (
        signals.rendered_text_present if isinstance(signals.rendered_text_present, bool) else None
    )

    if all(value is None for value in (extracted, ocr, hidden, offpage, duplicated, rendered)):
        return ExtractionIntegrityResult(
            ExtractionIntegrityStatus.REVIEW_REQUIRED,
            ("no extraction-integrity signals provided",),
        )

    reasons: list[str] = []
    failed = False
    review = False
    warning = False

    # Rendering shows text but extraction yields nothing: silence is NOT absence.
    if rendered is True and (extracted is None or extracted == 0):
        failed = True
        reasons.append("rendered text present but nothing extracted; 'not extracted' != 'absent'")

    # Hidden/invisible layers must never silently join the evidence base.
    if hidden is not None and hidden > 0:
        review = True
        reasons.append(f"hidden/invisible text detected ({hidden} chars); requires expert review")
    if offpage is not None and offpage > 0:
        review = True
        reasons.append(f"text outside page bounds ({offpage} chars); requires expert review")
    if duplicated is not None and duplicated > 0:
        review = True
        reasons.append(f"duplicated text layers ({duplicated}); requires expert review")

    # OCR and extraction disagree badly on a page that clearly has text.
    if extracted is not None and ocr is not None and ocr > 0:
        ratio = extracted / ocr
        if ratio < t.ocr_agreement_ratio:
            warning = True
            reasons.append(
                f"extracted/OCR char ratio {ratio:.2f} below "
                f"{t.ocr_agreement_ratio}; layers disagree"
            )

    if failed:
        return ExtractionIntegrityResult(ExtractionIntegrityStatus.FAILED, tuple(reasons))
    if review:
        return ExtractionIntegrityResult(ExtractionIntegrityStatus.REVIEW_REQUIRED, tuple(reasons))
    if warning:
        return ExtractionIntegrityResult(ExtractionIntegrityStatus.WARNING, tuple(reasons))

    # OK requires POSITIVE extraction evidence -- unknown extraction is not clean.
    if extracted is None:
        return ExtractionIntegrityResult(
            ExtractionIntegrityStatus.REVIEW_REQUIRED,
            ("extraction outcome unknown; cannot confirm integrity",),
        )
    if extracted == 0 and rendered is None:
        return ExtractionIntegrityResult(
            ExtractionIntegrityStatus.REVIEW_REQUIRED,
            ("nothing extracted and rendering evidence unknown; silence is not absence",),
        )
    return ExtractionIntegrityResult(
        ExtractionIntegrityStatus.OK, ("all known integrity signals consistent",)
    )


__all__ = [
    "ExtractionIntegrityResult",
    "ExtractionIntegritySignals",
    "ExtractionIntegrityStatus",
    "ExtractionIntegrityThresholds",
    "assess_extraction_integrity",
]
