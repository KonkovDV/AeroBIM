"""§3 layers 0-1: deterministic decision of whether/where a VLM runs (domain-pure).

Layer 0 — if a machine-readable text layer exists, the VLM is not invoked at all
(cheapest, fully reproducible). Layer 1 — otherwise each detected layout region
becomes ONE narrow read task (one region = one call); the whole sheet is never
sent to the VLM. This module is pure: no I/O, no image handling.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import DrawingRegionRef

# HeuristicLayoutRegionDetector stamp prior (normalized 0..1). Used as a
# defense-in-depth gate when layout_role is missing or mis-tagged.
_STAMP_PRIOR_XYXY = (0.55, 0.85, 1.0, 1.0)
_NORM_EPS = 1e-9


@dataclass(frozen=True)
class RegionReadTask:
    region_id: str
    bbox_xyxy: tuple[float, float, float, float]
    layout_role: str | None = None


@dataclass(frozen=True)
class RegionReadPlan:
    skip_vlm: bool
    reason: str
    tasks: tuple[RegionReadTask, ...] = ()
    stamp_regions_excluded: int = 0


def _is_normalized_bbox(bbox: tuple[float, float, float, float]) -> bool:
    return max(bbox) <= 1.0 + _NORM_EPS and min(bbox) >= 0.0 - _NORM_EPS


def _bbox_overlaps_stamp_prior(bbox: tuple[float, float, float, float]) -> bool:
    """True when a normalized crop substantially overlaps the stamp prior.

    Requires ≥50% of the crop area to lie inside the prior so a full-sheet
    content band (0,0)–(1,0.85) is not false-positive excluded.
    """
    if not _is_normalized_bbox(bbox):
        return False
    ax0, ay0, ax1, ay1 = bbox
    bx0, by0, bx1, by1 = _STAMP_PRIOR_XYXY
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return False
    inter = (ix1 - ix0) * (iy1 - iy0)
    area = max((ax1 - ax0) * (ay1 - ay0), _NORM_EPS)
    return (inter / area) >= 0.5


def is_stamp_like_region(region: DrawingRegionRef) -> bool:
    """PII-risk stamp gate: explicit role **or** normalized bbox stamp prior."""
    role = (region.layout_role or "").strip().lower()
    if role == "stamp":
        return True
    return _bbox_overlaps_stamp_prior(region.bbox_xyxy)


def plan_region_reads(
    *,
    text_layer_present: bool,
    regions: Sequence[DrawingRegionRef],
    exclude_stamp_regions: bool = True,
) -> RegionReadPlan:
    """Return the region-restricted read plan for one sheet (layers 0-1).

    When ``exclude_stamp_regions`` is true (default), stamp-like crops are not
    queued for cloud VLM — stamp fields often carry signatory PII (RESTRICTED
    without DPA / on-prem). Gate = ``layout_role=stamp`` **or** ≥50% overlap
    with the normalized stamp prior (defense in depth if a detector omits role).
    """
    if text_layer_present:
        return RegionReadPlan(
            skip_vlm=True,
            reason="Layer 0: machine-readable text layer present; VLM not invoked",
        )
    stamp_excluded = 0
    tasks_list: list[RegionReadTask] = []
    for index, region in enumerate(regions):
        role = (region.layout_role or "").strip().lower() or None
        if exclude_stamp_regions and is_stamp_like_region(region):
            stamp_excluded += 1
            continue
        tasks_list.append(
            RegionReadTask(
                region_id=f"r{index:02d}-{region.modality or 'region'}",
                bbox_xyxy=region.bbox_xyxy,
                layout_role=role,
            )
        )
    tasks = tuple(tasks_list)
    if not tasks:
        reason = "Layer 1: no layout regions detected; VLM not invoked"
        if stamp_excluded:
            reason = (
                f"Layer 1: only stamp region(s) remained after PII exclude "
                f"({stamp_excluded} skipped); VLM not invoked"
            )
        return RegionReadPlan(
            skip_vlm=True,
            reason=reason,
            stamp_regions_excluded=stamp_excluded,
        )
    reason = f"Layer 1: {len(tasks)} region(s) queued for region-restricted VLM"
    if stamp_excluded:
        reason += f"; excluded {stamp_excluded} stamp crop(s) (PII / RESTRICTED guard)"
    return RegionReadPlan(
        skip_vlm=False,
        reason=reason,
        tasks=tasks,
        stamp_regions_excluded=stamp_excluded,
    )


__all__ = [
    "RegionReadPlan",
    "RegionReadTask",
    "is_stamp_like_region",
    "plan_region_reads",
]
