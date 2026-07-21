"""I8c — escalate unmatched / low-confidence drawing regions for HITL (advisory).

Never affects ``summary.passed``. Cross-doc / Blueprint practice: unmatched zones
go to the expert, not silent ignore.

Geometric IoU match is **not** semantic match (RT-HYPER-005).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import replace
from typing import Literal

from aerobim.domain.models import (
    DrawingAnnotation,
    DrawingRegionRef,
    FindingCategory,
    ReviewEvent,
    Severity,
    ValidationIssue,
)

_DEFAULT_CONFIDENCE_FLOOR = 0.4
# Raised from 0.05 — tiny overlaps must not suppress HITL (geometric ≠ semantic).
_DEFAULT_IOU_MATCH = 0.25

BBoxValidationResult = Literal["ok", "invalid"]


def validate_bbox_xyxy(
    bbox: tuple[float, float, float, float] | list[float],
) -> tuple[BBoxValidationResult, str | None]:
    """Reject NaN/inf/inverted/zero-area boxes — never silently coerce."""

    if len(bbox) != 4:
        return "invalid", "bbox must have 4 coordinates"
    x0, y0, x1, y1 = (float(v) for v in bbox)
    for name, value in (("x0", x0), ("y0", y0), ("x1", x1), ("y1", y1)):
        if math.isnan(value) or math.isinf(value):
            return "invalid", f"{name} is not finite"
    if x0 < 0.0 or y0 < 0.0 or x1 < 0.0 or y1 < 0.0:
        return "invalid", "negative coordinates are not allowed"
    if x1 <= x0 or y1 <= y0:
        return "invalid", "bbox must have positive area with x1>x0 and y1>y0"
    return "ok", None


def intersection_over_union(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    return _iou(a, b)


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


def annotation_bbox_xyxy(ann: DrawingAnnotation) -> tuple[float, float, float, float] | None:
    """Public bbox helper for annotation↔region overlap."""

    return _annotation_bbox(ann)


def _annotation_bbox(ann: DrawingAnnotation) -> tuple[float, float, float, float] | None:
    zone = ann.problem_zone
    if zone is None:
        return None
    x = float(zone.x or 0.0)
    y = float(zone.y or 0.0)
    w = float(zone.width or 0.0)
    h = float(zone.height or 0.0)
    candidate = (x, y, x + w, y + h)
    status, _reason = validate_bbox_xyxy(candidate)
    if status != "ok":
        return None
    return candidate


def _region_fingerprint(region: DrawingRegionRef) -> str:
    bbox = ",".join(f"{v:.6f}" for v in region.bbox_xyxy)
    raw = (
        f"{region.sheet_id}|{region.modality}|{bbox}|"
        f"{region.confidence:.6f}|{region.hitl_reason or ''}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def mark_regions_for_hitl(
    regions: tuple[DrawingRegionRef, ...] | list[DrawingRegionRef],
    annotations: tuple[DrawingAnnotation, ...] | list[DrawingAnnotation] = (),
    *,
    confidence_floor: float = _DEFAULT_CONFIDENCE_FLOOR,
    iou_match: float = _DEFAULT_IOU_MATCH,
) -> tuple[DrawingRegionRef, ...]:
    """Flag detector/VLM regions that are low-confidence or unmatched to OCR annotations."""

    ann_boxes = [
        (ann.sheet_id, box) for ann in annotations if (box := _annotation_bbox(ann)) is not None
    ]
    enriched: list[DrawingRegionRef] = []
    for region in regions:
        reason: str | None = None
        bbox_status, bbox_reason = validate_bbox_xyxy(region.bbox_xyxy)
        if bbox_status != "ok":
            reason = f"invalid_bbox:{bbox_reason}"
        elif math.isnan(region.confidence) or math.isinf(region.confidence):
            reason = "invalid_confidence"
        elif region.confidence < 0.0 or region.confidence > 1.0:
            reason = "invalid_confidence"
        elif not (region.sheet_id or "").strip():
            reason = "empty_sheet_id"
        elif region.modality not in {"detector", "vlm", "ocr", "cad", "heuristic"}:
            reason = f"unknown_modality:{region.modality}"
        elif region.page_width is not None and (
            math.isnan(region.page_width) or math.isinf(region.page_width) or region.page_width <= 0
        ):
            reason = "invalid_page_width"
        elif region.page_height is not None and (
            math.isnan(region.page_height)
            or math.isinf(region.page_height)
            or region.page_height <= 0
        ):
            reason = "invalid_page_height"
        elif (
            region.page_width is not None
            and region.page_height is not None
            and (
                region.bbox_xyxy[2] > region.page_width + 1e-6
                or region.bbox_xyxy[3] > region.page_height + 1e-6
            )
        ):
            reason = "bbox_outside_page"
        elif region.modality in {"detector", "vlm"} and region.confidence < confidence_floor:
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
    """Emit deterministic escalation events (RT-HYPER-003).

    ``event_id`` is a stable hash of report_id + region fingerprint so re-analysis
    of the same input does not create duplicate HITL rows when de-duplicated by id.
    """

    events: list[ReviewEvent] = []
    for region in regions:
        if not region.hitl_required:
            continue
        fingerprint = _region_fingerprint(region)
        idem = f"hitl:{report_id}:{fingerprint}"
        event_id = hashlib.sha256(idem.encode("utf-8")).hexdigest()[:32]
        events.append(
            ReviewEvent(
                event_id=event_id,
                report_id=report_id,
                event_type="drawing_region_escalated",
                created_at=created_at,
                issue_rule_id="AEROBIM-DRAWING-REGION-HITL",
                actor="system",
                note=(
                    f"sheet={region.sheet_id}; modality={region.modality}; "
                    f"reason={region.hitl_reason}; conf={region.confidence:.3f}; "
                    f"bbox={region.bbox_xyxy}; geometric_iou_match_only=true"
                ),
                idempotency_key=idem,
            )
        )
    return events
