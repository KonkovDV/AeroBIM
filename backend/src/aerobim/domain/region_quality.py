"""Drawing-region quality gate (P1): bad/unknown quality is never 'no violations'.

Competitive P1 (AIDOX): before auto-reading a drawing region, assess its quality from
signals supplied by the ingestion/OCR layer (resolution/skew/text). A region of poor or
UNKNOWN quality must NOT be silently treated as «нарушений не найдено» — it is
UNREADABLE / LOW_QUALITY / REVIEW_REQUIRED and must be escalated to a human.

Honesty (coverage-map lesson): ``READABLE`` requires POSITIVE evidence (known-good
resolution + no negative trigger); unknown resolution -> REVIEW_REQUIRED, never a
default READABLE. Domain-pure; does NOT set ``summary.passed`` (ADR-001) — it gates
auto-reading, not the engineering verdict.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RegionQuality(StrEnum):
    READABLE = "readable"
    """Known-good resolution and no negative trigger — safe to auto-read."""
    LOW_QUALITY = "low_quality"
    """Degraded but not hopeless — auto-read result must be treated as advisory / HITL."""
    UNREADABLE = "unreadable"
    """Cannot be auto-read (too low DPI, too skewed, or no text) — expert required."""
    REVIEW_REQUIRED = "review_required"
    """Signals insufficient to confirm readability — expert required (never silent OK)."""


@dataclass(frozen=True)
class RegionQualitySignals:
    """Quality signals for a region (produced by the ingestion/OCR layer)."""

    dpi: float | None = None
    skew_deg: float | None = None
    has_text: bool | None = None
    text_char_count: int | None = None


@dataclass(frozen=True)
class RegionQualityThresholds:
    unreadable_dpi: float = 72.0
    low_dpi: float = 150.0
    unreadable_skew_deg: float = 15.0
    low_skew_deg: float = 3.0
    min_text_chars: int = 3


@dataclass(frozen=True)
class RegionQualityResult:
    quality: RegionQuality
    reasons: tuple[str, ...]

    def usable_for_auto_read(self) -> bool:
        """Only READABLE regions may be auto-read; everything else escalates to HITL."""
        return self.quality is RegionQuality.READABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "region-quality",
            "note": (
                "gates auto-reading of a drawing region; bad/unknown quality is NOT "
                "'no violations' — it escalates to a human; verdict-neutral (does NOT set "
                "summary.passed, ADR-001)"
            ),
            "quality": self.quality.value,
            "reasons": list(self.reasons),
            "usable_for_auto_read": self.usable_for_auto_read(),
        }


def _finite(value: float | None) -> float | None:
    """Treat None and non-finite (NaN/±inf) as UNKNOWN — never silently good."""
    return value if value is not None and math.isfinite(value) else None


def assess_region_quality(
    signals: RegionQualitySignals,
    thresholds: RegionQualityThresholds | None = None,
) -> RegionQualityResult:
    """Assess a region's quality (worst-severity wins; READABLE needs positive evidence)."""
    t = thresholds if thresholds is not None else RegionQualityThresholds()
    # Normalize non-finite (NaN/±inf) numeric signals to None: a corrupt/failed
    # measurement is UNKNOWN, never silently good (NaN comparisons are all False,
    # which would otherwise fall through to READABLE — the exact hole this gate closes).
    dpi = _finite(signals.dpi)
    skew_deg = _finite(signals.skew_deg)
    if all(value is None for value in (dpi, skew_deg, signals.has_text, signals.text_char_count)):
        return RegionQualityResult(RegionQuality.REVIEW_REQUIRED, ("no quality signals provided",))

    verdicts: list[RegionQuality] = []
    reasons: list[str] = []

    if dpi is not None:
        if dpi < t.unreadable_dpi:
            verdicts.append(RegionQuality.UNREADABLE)
            reasons.append(f"dpi {dpi} below unreadable floor {t.unreadable_dpi}")
        elif dpi < t.low_dpi:
            verdicts.append(RegionQuality.LOW_QUALITY)
            reasons.append(f"dpi {dpi} below recommended {t.low_dpi}")

    if skew_deg is not None:
        skew = abs(skew_deg)
        if skew > t.unreadable_skew_deg:
            verdicts.append(RegionQuality.UNREADABLE)
            reasons.append(f"skew {skew}° exceeds unreadable max {t.unreadable_skew_deg}°")
        elif skew > t.low_skew_deg:
            verdicts.append(RegionQuality.LOW_QUALITY)
            reasons.append(f"skew {skew}° exceeds recommended {t.low_skew_deg}°")

    if signals.has_text is False:
        verdicts.append(RegionQuality.UNREADABLE)
        reasons.append("no text detected in region")
    elif signals.text_char_count is not None and signals.text_char_count < t.min_text_chars:
        verdicts.append(RegionQuality.LOW_QUALITY)
        reasons.append(f"text chars {signals.text_char_count} below minimum {t.min_text_chars}")

    if RegionQuality.UNREADABLE in verdicts:
        return RegionQualityResult(RegionQuality.UNREADABLE, tuple(reasons))
    if RegionQuality.LOW_QUALITY in verdicts:
        return RegionQualityResult(RegionQuality.LOW_QUALITY, tuple(reasons))

    # No negative trigger. READABLE requires POSITIVE resolution evidence — otherwise
    # we cannot confirm readability and must fail safe to expert review.
    if dpi is None:
        return RegionQualityResult(
            RegionQuality.REVIEW_REQUIRED,
            ("resolution unknown or invalid; cannot confirm readable",),
        )
    return RegionQualityResult(
        RegionQuality.READABLE, ("all known quality signals within thresholds",)
    )


__all__ = [
    "RegionQuality",
    "RegionQualityResult",
    "RegionQualitySignals",
    "RegionQualityThresholds",
    "assess_region_quality",
]
