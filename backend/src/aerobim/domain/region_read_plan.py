"""§3 layers 0-1: deterministic decision of whether/where a VLM runs (domain-pure).

Layer 0 — if a machine-readable text layer exists, the VLM is not invoked at all
(cheapest, fully reproducible). Layer 1 — otherwise each detected layout region
becomes ONE narrow read task (one region = one call); the whole sheet is never
sent to the VLM. This module is pure: no I/O, no image handling.

Cloud PII doctrine (aligned with ``data_classification`` / trust fail-closed):
allowlist roles safe to send; unknown / stamp / title_block are excluded; for
allowlisted crops, subtract layout PII priors (stamp + title block) from the
bbox so a whole-sheet content crop cannot smuggle signatory ФИО.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import DrawingRegionRef

# Only these roles may leave the contour toward cloud VLM (after PII prior clip).
_CLOUD_SAFE_LAYOUT_ROLES = frozenset({"content"})

# HeuristicLayoutRegionDetector PII priors (normalized 0..1). Subtracted from
# allowlisted crops so oversized boxes (incl. full sheet) cannot carry stamp /
# main-inscription ФИО. Not a complete ГОСТ geometry model (RT-STAMP-06).
_PII_LAYOUT_PRIORS: tuple[tuple[float, float, float, float], ...] = (
    (0.55, 0.85, 1.0, 1.0),  # stamp (lower-right)
    (0.0, 0.85, 0.25, 1.0),  # title block / основная надпись (lower-left)
)
_NORM_EPS = 1e-9
_MIN_EDGE = 1e-4

BBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class RegionReadTask:
    region_id: str
    bbox_xyxy: BBox
    layout_role: str | None = None


@dataclass(frozen=True)
class RegionReadPlan:
    skip_vlm: bool
    reason: str
    tasks: tuple[RegionReadTask, ...] = ()
    stamp_regions_excluded: int = 0


def _is_normalized_bbox(bbox: BBox) -> bool:
    return max(bbox) <= 1.0 + _NORM_EPS and min(bbox) >= 0.0 - _NORM_EPS


def _bbox_area(bbox: BBox) -> float:
    return max(bbox[2] - bbox[0], 0.0) * max(bbox[3] - bbox[1], 0.0)


def subtract_aabb(outer: BBox, hole: BBox) -> tuple[BBox, ...]:
    """Axis-aligned set difference ``outer \\ hole`` as up to four rectangles."""
    ax0, ay0, ax1, ay1 = outer
    bx0, by0, bx1, by1 = hole
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 + _NORM_EPS or iy1 <= iy0 + _NORM_EPS:
        return (outer,)
    if (
        ix0 <= ax0 + _NORM_EPS
        and iy0 <= ay0 + _NORM_EPS
        and ix1 >= ax1 - _NORM_EPS
        and iy1 >= ay1 - _NORM_EPS
    ):
        return ()
    parts: list[BBox] = []
    if ay0 < iy0 - _NORM_EPS:
        parts.append((ax0, ay0, ax1, iy0))
    if iy1 < ay1 - _NORM_EPS:
        parts.append((ax0, iy1, ax1, ay1))
    if ax0 < ix0 - _NORM_EPS:
        parts.append((ax0, iy0, ix0, iy1))
    if ix1 < ax1 - _NORM_EPS:
        parts.append((ix1, iy0, ax1, iy1))
    return tuple(p for p in parts if _bbox_area(p) > _MIN_EDGE * _MIN_EDGE)


def clip_pii_priors(bbox: BBox) -> tuple[BBox, ...]:
    """Subtract all PII layout priors from a normalized bbox."""
    remaining: tuple[BBox, ...] = (bbox,)
    for prior in _PII_LAYOUT_PRIORS:
        next_parts: list[BBox] = []
        for piece in remaining:
            next_parts.extend(subtract_aabb(piece, prior))
        remaining = tuple(next_parts)
    return remaining


def _normalized_bbox(region: DrawingRegionRef) -> BBox | None:
    """Return 0..1 bbox, or None when coordinates cannot be trusted for clipping."""
    bbox = region.bbox_xyxy
    if _is_normalized_bbox(bbox):
        return bbox
    pw, ph = region.page_width, region.page_height
    if pw is not None and ph is not None and pw > 0 and ph > 0:
        x0, y0, x1, y1 = bbox
        return (x0 / pw, y0 / ph, x1 / pw, y1 / ph)
    return None


def is_cloud_safe_layout_role(role: str | None) -> bool:
    return (role or "").strip().lower() in _CLOUD_SAFE_LAYOUT_ROLES


def is_stamp_like_region(region: DrawingRegionRef) -> bool:
    """True when the region must not be sent as-is under the PII guard.

    Kept for callers/tests: not on the cloud-safe allowlist, or normalized crop
    still intersects a PII prior before clipping.
    """
    role = (region.layout_role or "").strip().lower() or None
    if not is_cloud_safe_layout_role(role):
        return True
    norm = _normalized_bbox(region)
    if norm is None:
        return True
    clipped = clip_pii_priors(norm)
    return clipped != (norm,)


def plan_region_reads(
    *,
    text_layer_present: bool,
    regions: Sequence[DrawingRegionRef],
    exclude_stamp_regions: bool = True,
) -> RegionReadPlan:
    """Return the region-restricted read plan for one sheet (layers 0-1).

    When ``exclude_stamp_regions`` is true (default) the cloud PII guard applies:

    1. **Allowlist** — only ``layout_role=content`` may be queued (unknown /
       stamp / title_block → exclude). Matches ``data_classification`` doctrine:
       unknown does not lower restriction.
    2. **Clip** — allowlisted bboxes have PII priors subtracted (not overlap-
       ratio discard), so a full-sheet content crop cannot pass stamp ФИО.
    3. **Fail-closed coordinates** — non-normalized bbox without page size
       cannot be clipped → exclude even if role is ``content``.
    """
    if text_layer_present:
        return RegionReadPlan(
            skip_vlm=True,
            reason="Layer 0: machine-readable text layer present; VLM not invoked",
        )
    excluded = 0
    tasks_list: list[RegionReadTask] = []
    for index, region in enumerate(regions):
        role = (region.layout_role or "").strip().lower() or None
        modality = region.modality or "region"
        if not exclude_stamp_regions:
            tasks_list.append(
                RegionReadTask(
                    region_id=f"r{index:02d}-{modality}",
                    bbox_xyxy=region.bbox_xyxy,
                    layout_role=role,
                )
            )
            continue

        if not is_cloud_safe_layout_role(role):
            excluded += 1
            continue

        norm = _normalized_bbox(region)
        if norm is None:
            # Pixel / unknown CRS without page size: cannot clip priors → deny.
            excluded += 1
            continue

        residuals = clip_pii_priors(norm)
        if not residuals:
            excluded += 1
            continue

        for part_i, part in enumerate(residuals):
            suffix = "" if len(residuals) == 1 else f"-c{part_i}"
            tasks_list.append(
                RegionReadTask(
                    region_id=f"r{index:02d}-{modality}{suffix}",
                    bbox_xyxy=part,
                    layout_role=role,
                )
            )

    tasks = tuple(tasks_list)
    if not tasks:
        reason = "Layer 1: no layout regions detected; VLM not invoked"
        if excluded:
            reason = (
                f"Layer 1: no cloud-safe regions after PII allowlist/clip "
                f"({excluded} excluded); VLM not invoked"
            )
        return RegionReadPlan(
            skip_vlm=True,
            reason=reason,
            stamp_regions_excluded=excluded,
        )
    reason = f"Layer 1: {len(tasks)} region(s) queued for region-restricted VLM"
    if excluded:
        reason += f"; excluded {excluded} non-allowlisted / unclippable crop(s) (PII guard)"
    return RegionReadPlan(
        skip_vlm=False,
        reason=reason,
        tasks=tasks,
        stamp_regions_excluded=excluded,
    )


__all__ = [
    "RegionReadPlan",
    "RegionReadTask",
    "clip_pii_priors",
    "is_cloud_safe_layout_role",
    "is_stamp_like_region",
    "plan_region_reads",
    "subtract_aabb",
]
