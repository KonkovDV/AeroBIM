"""Drawing-region assessment (P1): compose the quality gate + type classifier.

Verdict-neutral orchestration of the two P1 drawing primitives into one honest decision:
1) assess region quality; 2) ONLY if the region is auto-readable, classify its type.

Honesty: a non-readable region is NEVER classified (its OCR text is unreliable — a label
built on it would be a guess) and NEVER auto-read; ``AUTO_READ`` requires BOTH a READABLE
quality AND a known type — anything else is ``EXPERT_REVIEW``. Domain-pure; does NOT set
``summary.passed`` (ADR-001) — it decides whether the pipeline may auto-read a region,
not the engineering verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from aerobim.domain.region_classifier import RegionClassification, classify_region
from aerobim.domain.region_quality import (
    RegionQuality,
    RegionQualitySignals,
    RegionQualityThresholds,
    assess_region_quality,
)


class RegionAction(StrEnum):
    AUTO_READ = "auto_read"
    """Readable AND confidently typed — the pipeline may auto-read (still advisory)."""
    EXPERT_REVIEW = "expert_review"
    """Not readable, or type undetermined — escalate to a human (never a silent read)."""


@dataclass(frozen=True)
class DrawingRegionAssessment:
    quality: RegionQuality
    classification: RegionClassification | None
    action: RegionAction
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "drawing-region-assessment",
            "note": (
                "quality gate + type classifier composition; a non-readable region is not "
                "classified and not auto-read; AUTO_READ needs readable + known type; "
                "verdict-neutral (does NOT set summary.passed, ADR-001)"
            ),
            "quality": self.quality.value,
            "classification": (
                self.classification.to_dict() if self.classification is not None else None
            ),
            "action": self.action.value,
            "reasons": list(self.reasons),
        }


def assess_drawing_region(
    *,
    text: str | None = None,
    quality_signals: RegionQualitySignals | None = None,
    quality_thresholds: RegionQualityThresholds | None = None,
    has_table_structure: bool | None = None,
    numeric_ratio: float | None = None,
) -> DrawingRegionAssessment:
    """Assess a drawing region: quality first, then type only if auto-readable.

    Returns AUTO_READ only when quality is READABLE AND a type is confidently known;
    a non-readable region is left unclassified and routed to EXPERT_REVIEW (its text is
    not trustworthy enough to auto-label). Verdict-neutral.
    """
    quality = assess_region_quality(quality_signals or RegionQualitySignals(), quality_thresholds)
    if not quality.usable_for_auto_read():
        return DrawingRegionAssessment(
            quality=quality.quality,
            classification=None,
            action=RegionAction.EXPERT_REVIEW,
            reasons=(f"region not auto-readable (quality={quality.quality.value})",),
        )

    classification = classify_region(
        text, has_table_structure=has_table_structure, numeric_ratio=numeric_ratio
    )
    if not classification.is_known():
        return DrawingRegionAssessment(
            quality=quality.quality,
            classification=classification,
            action=RegionAction.EXPERT_REVIEW,
            reasons=("region type could not be determined (no match or ambiguous)",),
        )

    return DrawingRegionAssessment(
        quality=quality.quality,
        classification=classification,
        action=RegionAction.AUTO_READ,
        reasons=(f"readable and typed as {classification.region_type.value}",),
    )


__all__ = [
    "DrawingRegionAssessment",
    "RegionAction",
    "assess_drawing_region",
]
