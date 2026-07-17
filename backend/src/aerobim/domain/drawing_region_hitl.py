"""I8c — escalate unmatched / low-confidence drawing regions for HITL (advisory).

Never affects ``summary.passed``. Cross-doc / Blueprint practice: unmatched zones
go to the expert, not silent ignore.
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from aerobim.domain.models import (
    DrawingAnnotation,
    DrawingRegionRef,
    FindingCategory,
    ReviewEvent,
    Severity,
    ValidationIssue,
)

_DEFAULT_CONFIDENCE_FLOOR = 0.4


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    area_a = max(0.0, ax1 - ax0) * max(0.0, ay1 - ay0)
    area_b = max(0.0, bx1 - bx0) * max(0.0, by1 - by0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _annotation_bbox(ann: DrawingAnnotation) -> tuple[float, float, float, float] | None:
    zone = ann.problem_zone
    if zone is None:
        return None
    x = float(zone.x or 0.0)
    y = float(zone.y or 0.0)
    w = float(zone.width or 0.0)
    h = float(zone.height or 0.0)
    return (x, y, x + w, y + h)


def mark_regions_for_hitl(
    regions: tuple[DrawingRegionRef, ...] | list[DrawingRegionRef],
    annotations: tuple[DrawingAnnotation, ...] | list[DrawingAnnotation] = (),
    *,
    confidence_floor: float = _DEFAULT_CONFIDENCE_FLOOR,
    iou_match: float = 0.05,
) -> tuple[DrawingRegionRef, ...]:
    """Flag detector/VLM regions that are low-confidence or unmatched to OCR annotations."""

    ann_boxes = [
        (ann.sheet_id, box) for ann in annotations if (box := _annotation_bbox(ann)) is not None
    ]
    enriched: list[DrawingRegionRef] = []
    for region in regions:
        reason: str | None = None
        if region.modality in {"detector", "vlm"} and region.confidence < confidence_floor:
            reason = f"low_confidence<{confidence_floor}"
        elif region.modality == "detector":
            matched = False
            for sheet_id, box in ann_boxes:
                if sheet_id != region.sheet_id:
                    continue
                if _iou(region.bbox_xyxy, box) >= iou_match:
                    matched = True
                    break
            if not matched and annotations:
                reason = "unmatched_to_ocr_annotations"
            elif not matched and not annotations:
                reason = "detector_without_ocr_coverage"
        if reason is None:
            enriched.append(region)
        else:
            enriched.append(replace(region, hitl_required=True, hitl_reason=reason))
    return tuple(enriched)


def issues_for_hitl_regions(
    regions: tuple[DrawingRegionRef, ...] | list[DrawingRegionRef],
) -> list[ValidationIssue]:
    """INFO issues for triage panel — never ERROR (does not block pass alone)."""

    issues: list[ValidationIssue] = []
    for region in regions:
        if not region.hitl_required:
            continue
        issues.append(
            ValidationIssue(
                rule_id="AEROBIM-DRAWING-REGION-HITL",
                severity=Severity.INFO,
                message=(
                    f"Drawing region on {region.sheet_id} requires expert review "
                    f"({region.hitl_reason or 'unmatched'}); modality={region.modality}"
                ),
                category=FindingCategory.CROSS_DOCUMENT,
                source_id=region.sheet_id,
                evidence_modality=region.modality,
                confidence=region.confidence,
                evidence_refs=(
                    f"region@{region.sheet_id}#"
                    f"{region.bbox_xyxy[0]:.3f},{region.bbox_xyxy[1]:.3f},"
                    f"{region.bbox_xyxy[2]:.3f},{region.bbox_xyxy[3]:.3f}",
                ),
            )
        )
    return issues


def review_events_for_hitl_regions(
    *,
    report_id: str,
    regions: tuple[DrawingRegionRef, ...] | list[DrawingRegionRef],
    created_at: str,
) -> list[ReviewEvent]:
    events: list[ReviewEvent] = []
    for region in regions:
        if not region.hitl_required:
            continue
        events.append(
            ReviewEvent(
                event_id=uuid4().hex,
                report_id=report_id,
                event_type="drawing_region_escalated",
                created_at=created_at,
                issue_rule_id="AEROBIM-DRAWING-REGION-HITL",
                actor="system",
                note=(
                    f"sheet={region.sheet_id}; modality={region.modality}; "
                    f"reason={region.hitl_reason}; conf={region.confidence:.3f}; "
                    f"bbox={region.bbox_xyxy}"
                ),
            )
        )
    return events
