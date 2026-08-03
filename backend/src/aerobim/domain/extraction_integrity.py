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
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aerobim.domain.models import CapabilityStatus

# Numeric spoof class (visual «3000» vs text-layer «3300»): char-count ratios miss
# same-length substitutions. Collide digit runs of this length across channels.
_DIGIT_RUN_RE = re.compile(r"\d{3,}")


def extract_digit_runs(text: str) -> tuple[str, ...]:
    """Sorted unique digit runs (≥3 digits) for deterministic channel collision.

    Uniqueness avoids false FAILED from pdfminer/OCR duplicate spans of the same
    number; the spoof class is different values (visual «3000» vs text «3300»).
    """

    return tuple(sorted(set(_DIGIT_RUN_RE.findall(text or ""))))


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
    extracted_digit_runs: tuple[str, ...] | None = None
    """Digit runs (≥3) from text-layer; None = channel not measured."""
    ocr_digit_runs: tuple[str, ...] | None = None
    """Digit runs (≥3) from OCR on rendered pages; None = OCR not measured."""


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

    def to_capability_status(self) -> CapabilityStatus:
        """Map integrity assessment onto report capability vocabulary.

        CapabilityState has no REVIEW_REQUIRED/WARNING — those become NOT_VERIFIED
        (expert attention) without silently looking like OK. FAILED stays FAILED
        (pass-blocking). OK stays OK.
        """

        from aerobim.domain.models import CapabilityState, CapabilityStatus

        reason = "; ".join(self.reasons) if self.reasons else None
        if self.status is ExtractionIntegrityStatus.OK:
            return CapabilityStatus(
                CapabilityState.OK,
                reason or "PDF text-layer signals consistent",
            )
        if self.status is ExtractionIntegrityStatus.FAILED:
            return CapabilityStatus(CapabilityState.FAILED, reason)
        # warning / review_required → not_verified (usable only with expert eyes)
        return CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            reason or f"extraction-integrity={self.status.value}",
        )

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
    text_digits = signals.extracted_digit_runs
    ocr_digits = signals.ocr_digit_runs
    if text_digits is not None and not isinstance(text_digits, tuple):
        text_digits = None
    if ocr_digits is not None and not isinstance(ocr_digits, tuple):
        ocr_digits = None

    if all(
        value is None
        for value in (
            extracted,
            ocr,
            hidden,
            offpage,
            duplicated,
            rendered,
            text_digits,
            ocr_digits,
        )
    ):
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

    # Channel collision: text-layer vs OCR digit runs (same-length spoof: 3000 vs 3300).
    if text_digits is not None and ocr_digits is not None:
        text_set = set(text_digits)
        ocr_set = set(ocr_digits)
        if text_set and ocr_set and text_set != ocr_set:
            failed = True
            reasons.append(
                "text-layer vs OCR digit-run mismatch "
                f"(text={sorted(text_set)}, ocr={sorted(ocr_set)}); "
                "extracted numerics must not be trusted for cross-doc"
            )
        elif bool(text_set) != bool(ocr_set):
            warning = True
            reasons.append(
                "digit runs present on only one channel "
                f"(text={len(text_set)}, ocr={len(ocr_set)}); layers disagree"
            )

    # OCR and extraction disagree badly on volume (char-count only — misses same-len spoof).
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


_STATUS_RANK = {
    ExtractionIntegrityStatus.OK: 0,
    ExtractionIntegrityStatus.WARNING: 1,
    ExtractionIntegrityStatus.REVIEW_REQUIRED: 2,
    ExtractionIntegrityStatus.FAILED: 3,
}


def merge_integrity_results(
    results: tuple[ExtractionIntegrityResult, ...],
) -> ExtractionIntegrityResult:
    """Worst-severity wins across PDF sources in one package."""

    if not results:
        return ExtractionIntegrityResult(
            ExtractionIntegrityStatus.REVIEW_REQUIRED,
            ("no extraction-integrity results",),
        )
    worst = max(results, key=lambda item: _STATUS_RANK[item.status])
    reasons: list[str] = []
    for item in results:
        reasons.extend(item.reasons)
    return ExtractionIntegrityResult(worst.status, tuple(dict.fromkeys(reasons)))


__all__ = [
    "ExtractionIntegrityResult",
    "ExtractionIntegritySignals",
    "ExtractionIntegrityStatus",
    "ExtractionIntegrityThresholds",
    "assess_extraction_integrity",
    "extract_digit_runs",
    "merge_integrity_results",
]
