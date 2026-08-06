"""§3 layers 0-1: deterministic decision of whether/where a VLM runs (domain-pure).

Layer 0 — if a machine-readable text layer exists, the VLM is not invoked at all
(cheapest, fully reproducible). Layer 1 — otherwise each detected layout region
becomes ONE narrow read task (one region = one call); the whole sheet is never
sent to the VLM. This module is pure: no I/O, no image handling.

Cloud PII doctrine (aligned with ``data_classification`` / trust fail-closed):
allowlist roles safe to send; unknown roles excluded with a coverage signal;
allowlisted crops have visual PII priors subtracted after mapping by PDF
``/Rotate``; absolute CRS overflow and unknown rotation fail closed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import DrawingRegionRef

# Only these roles may leave the contour toward cloud VLM (after PII prior clip).
_CLOUD_SAFE_LAYOUT_ROLES = frozenset({"content"})
# Expected non-content roles from the heuristic detector (not a coverage alarm).
_EXPECTED_BLOCKED_ROLES = frozenset({"stamp", "title_block"})

# Visual-orientation priors (normalized 0..1, y-down). Mapped into page space
# via ``page_rotate_degrees`` before clipping (RT-STAMP-14).
_PII_LAYOUT_PRIORS_VISUAL: tuple[tuple[float, float, float, float], ...] = (
    (0.0, 0.85, 1.0, 1.0),  # bottom inscription / stamp
    (0.0, 0.0, 0.10, 1.0),  # left vertical title strip
)
_ALLOWED_ROTATIONS = frozenset({0, 90, 180, 270})
_ABSOLUTE_CRS = frozenset(
    {
        "page-point",
        "page-points",
        "page-pixel",
        "page-pixels",
        "px",
        "pt",
        "points",
    }
)
_NORMALIZED_CRS_ALIASES = frozenset({"normalized-0-1", "normalized", "rel", "relative"})
_NORM_EPS = 1e-9
_MIN_EDGE = 1e-4
# Outside [0,1] by more than this → CRS/CropBox desync (RT-STAMP-15).
_OVERFLOW_TOL = 0.02
# If clamping removes more than 1% of bbox area → treat as CRS desync (RT-STAMP-15).
_CLAMP_AREA_CHANGE_MAX = 0.01

BBox = tuple[float, float, float, float]
_NORMALIZED_CRS = "normalized-0-1"


@dataclass(frozen=True)
class RegionReadTask:
    region_id: str
    bbox_xyxy: BBox
    layout_role: str | None = None
    coordinate_system: str = _NORMALIZED_CRS


@dataclass(frozen=True)
class RegionReadPlan:
    skip_vlm: bool
    reason: str
    tasks: tuple[RegionReadTask, ...] = ()
    stamp_regions_excluded: int = 0
    """Total excluded under PII guard (back-compat sum of role + geometry)."""
    excluded_by_role: int = 0
    """Not on cloud-safe allowlist (stamp/title/unknown)."""
    excluded_by_crs: int = 0
    """Unusable coordinates / absolute CRS / overflow (RT-STAMP-15/16)."""
    excluded_by_pii_clip: int = 0
    """Allowlisted region empty after PII prior clip."""
    excluded_by_geometry: int = 0
    """Back-compat sum of ``excluded_by_crs`` + ``excluded_by_pii_clip``."""
    excluded_unknown_role: int = 0
    """Subset of role excludes that are not stamp/title_block (coverage alarm)."""


def _is_normalized_bbox(bbox: BBox) -> bool:
    return max(bbox) <= 1.0 + _NORM_EPS and min(bbox) >= 0.0 - _NORM_EPS


def _is_valid_bbox(bbox: BBox) -> bool:
    return bbox[2] - bbox[0] > _MIN_EDGE and bbox[3] - bbox[1] > _MIN_EDGE


def _bbox_area(bbox: BBox) -> float:
    return max(bbox[2] - bbox[0], 0.0) * max(bbox[3] - bbox[1], 0.0)


def _crs_token(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


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


def _map_point_visual_to_page(x: float, y: float, rotate_cw: int) -> tuple[float, float]:
    """Map a visual (display) point into unrotated page-normalized coords."""
    if rotate_cw == 0:
        return x, y
    if rotate_cw == 90:
        # Visual bottom ← page left; visual left ← page bottom.
        return (1.0 - y, x)
    if rotate_cw == 180:
        return (1.0 - x, 1.0 - y)
    if rotate_cw == 270:
        return (y, 1.0 - x)
    raise ValueError(f"unsupported rotate {rotate_cw}")


def priors_in_page_space(page_rotate_degrees: int) -> tuple[BBox, ...]:
    """Rotate visual PII priors into page-normalized space (AABB of corners)."""
    rotate = int(page_rotate_degrees) % 360
    if rotate not in _ALLOWED_ROTATIONS:
        raise ValueError(f"unsupported page rotation {page_rotate_degrees}")
    mapped: list[BBox] = []
    for x0, y0, x1, y1 in _PII_LAYOUT_PRIORS_VISUAL:
        corners = (
            _map_point_visual_to_page(x0, y0, rotate),
            _map_point_visual_to_page(x1, y0, rotate),
            _map_point_visual_to_page(x0, y1, rotate),
            _map_point_visual_to_page(x1, y1, rotate),
        )
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        box = (_clamp01(min(xs)), _clamp01(min(ys)), _clamp01(max(xs)), _clamp01(max(ys)))
        if _is_valid_bbox(box):
            mapped.append(box)
    return tuple(mapped)


def clip_pii_priors(bbox: BBox, *, page_rotate_degrees: int = 0) -> tuple[BBox, ...]:
    """Subtract PII priors (visual, mapped by ``/Rotate``) from a page-normalized bbox."""
    remaining: tuple[BBox, ...] = (bbox,)
    for prior in priors_in_page_space(page_rotate_degrees):
        next_parts: list[BBox] = []
        for piece in remaining:
            next_parts.extend(subtract_aabb(piece, prior))
        remaining = tuple(next_parts)
    return remaining


def _finalize_normalized(norm: BBox) -> BBox | None:
    """Clamp to [0,1]; reject significant out-of-page overflow (RT-STAMP-15)."""
    if any(c < -_OVERFLOW_TOL or c > 1.0 + _OVERFLOW_TOL for c in norm):
        return None
    raw_area = _bbox_area(norm)
    clamped = (_clamp01(norm[0]), _clamp01(norm[1]), _clamp01(norm[2]), _clamp01(norm[3]))
    x0, y0 = min(clamped[0], clamped[2]), min(clamped[1], clamped[3])
    x1, y1 = max(clamped[0], clamped[2]), max(clamped[1], clamped[3])
    ordered = (x0, y0, x1, y1)
    if not _is_valid_bbox(ordered):
        return None
    clamped_area = _bbox_area(ordered)
    if raw_area > _MIN_EDGE * _MIN_EDGE:
        lost = abs(raw_area - clamped_area) / raw_area
        if lost > _CLAMP_AREA_CHANGE_MAX:
            return None
    return ordered


def _scale_to_normalized(bbox: BBox, page_width: float, page_height: float) -> BBox | None:
    x0, y0, x1, y1 = bbox
    norm = (x0 / page_width, y0 / page_height, x1 / page_width, y1 / page_height)
    return _finalize_normalized(norm)


def _normalized_bbox(region: DrawingRegionRef) -> BBox | None:
    """Return page-normalized 0..1 bbox, or None when coordinates are untrusted."""
    bbox = region.bbox_xyxy
    if not _is_valid_bbox(bbox):
        return None
    crs = _crs_token(region.coordinate_system)
    pw, ph = region.page_width, region.page_height
    has_page = pw is not None and ph is not None and pw > 0 and ph > 0

    if crs in _ABSOLUTE_CRS:
        if not has_page:
            return None
        assert pw is not None and ph is not None
        return _scale_to_normalized(bbox, float(pw), float(ph))

    if crs in _NORMALIZED_CRS_ALIASES:
        return _finalize_normalized(bbox) if min(bbox) >= -_OVERFLOW_TOL else None

    if _is_normalized_bbox(bbox):
        return _finalize_normalized(bbox)
    if has_page:
        assert pw is not None and ph is not None
        return _scale_to_normalized(bbox, float(pw), float(ph))
    return None


def is_cloud_safe_layout_role(role: str | None) -> bool:
    return (role or "").strip().lower() in _CLOUD_SAFE_LAYOUT_ROLES


def is_stamp_like_region(region: DrawingRegionRef, *, page_rotate_degrees: int = 0) -> bool:
    """True when the region must not be sent as-is under the PII guard."""
    role = (region.layout_role or "").strip().lower() or None
    if not is_cloud_safe_layout_role(role):
        return True
    if page_rotate_degrees not in _ALLOWED_ROTATIONS:
        return True
    norm = _normalized_bbox(region)
    if norm is None:
        return True
    clipped = clip_pii_priors(norm, page_rotate_degrees=page_rotate_degrees)
    return clipped != (norm,)


def plan_region_reads(
    *,
    text_layer_present: bool,
    regions: Sequence[DrawingRegionRef],
    exclude_stamp_regions: bool = True,
    page_rotate_degrees: int | None = 0,
) -> RegionReadPlan:
    """Return the region-restricted read plan for one sheet (layers 0-1).

    When ``exclude_stamp_regions`` is true (default) the cloud PII guard applies:

    1. **Allowlist** — only ``layout_role=content`` may be queued.
    2. **Rotate** — PII priors are visual; ``page_rotate_degrees`` maps them into
       page space. ``None`` / unsupported → fail-closed (RT-STAMP-14).
    3. **Clip** — allowlisted bboxes have mapped priors subtracted.
    4. **Overflow** — coords beyond [0,1] by >2% → exclude (RT-STAMP-15).
    5. Counters split role vs geometry vs unknown-role coverage (RT-STAMP-16).
    """
    if text_layer_present:
        return RegionReadPlan(
            skip_vlm=True,
            reason="Layer 0: machine-readable text layer present; VLM not invoked",
        )

    excluded_role = 0
    excluded_crs = 0
    excluded_clip = 0
    excluded_unknown = 0
    tasks_list: list[RegionReadTask] = []

    if exclude_stamp_regions and (
        page_rotate_degrees is None or int(page_rotate_degrees) % 360 not in _ALLOWED_ROTATIONS
    ):
        n = len(regions)
        return RegionReadPlan(
            skip_vlm=True,
            reason=(
                "Layer 1: unknown/unsupported page /Rotate — PII priors unsafe; "
                "VLM not invoked (fail-closed)"
            ),
            stamp_regions_excluded=n,
            excluded_by_crs=n,
            excluded_by_geometry=n,
        )

    rotate = 0 if page_rotate_degrees is None else int(page_rotate_degrees) % 360

    for index, region in enumerate(regions):
        role = (region.layout_role or "").strip().lower() or None
        modality = region.modality or "region"
        if not exclude_stamp_regions:
            crs = (
                region.coordinate_system
                if region.coordinate_system
                else ("normalized-0-1" if _is_normalized_bbox(region.bbox_xyxy) else "page-point")
            )
            tasks_list.append(
                RegionReadTask(
                    region_id=f"r{index:02d}-{modality}",
                    bbox_xyxy=region.bbox_xyxy,
                    layout_role=role,
                    coordinate_system=crs,
                )
            )
            continue

        if not is_cloud_safe_layout_role(role):
            excluded_role += 1
            if role not in _EXPECTED_BLOCKED_ROLES:
                excluded_unknown += 1
            continue

        norm = _normalized_bbox(region)
        if norm is None:
            excluded_crs += 1
            continue

        residuals = clip_pii_priors(norm, page_rotate_degrees=rotate)
        if not residuals:
            excluded_clip += 1
            continue

        for part_i, part in enumerate(residuals):
            suffix = "" if len(residuals) == 1 else f"-c{part_i}"
            tasks_list.append(
                RegionReadTask(
                    region_id=f"r{index:02d}-{modality}{suffix}",
                    bbox_xyxy=part,
                    layout_role=role,
                    coordinate_system=_NORMALIZED_CRS,
                )
            )

    excluded_geom = excluded_crs + excluded_clip
    excluded_total = excluded_role + excluded_geom
    tasks = tuple(tasks_list)
    if not tasks:
        reason = "Layer 1: no layout regions detected; VLM not invoked"
        if excluded_total:
            reason = (
                f"Layer 1: no cloud-safe regions after PII allowlist/clip "
                f"(role={excluded_role}, crs={excluded_crs}, pii_clip={excluded_clip}"
                f"{f', unknown_role={excluded_unknown}' if excluded_unknown else ''}"
                f"); VLM not invoked"
            )
        return RegionReadPlan(
            skip_vlm=True,
            reason=reason,
            stamp_regions_excluded=excluded_total,
            excluded_by_role=excluded_role,
            excluded_by_crs=excluded_crs,
            excluded_by_pii_clip=excluded_clip,
            excluded_by_geometry=excluded_geom,
            excluded_unknown_role=excluded_unknown,
        )
    reason = f"Layer 1: {len(tasks)} region(s) queued for region-restricted VLM"
    if excluded_total:
        reason += (
            f"; excluded role={excluded_role} crs={excluded_crs} "
            f"pii_clip={excluded_clip}"
            f"{f' unknown_role={excluded_unknown}' if excluded_unknown else ''} (PII guard)"
        )
    if excluded_unknown:
        reason += "; coverage alarm: unexpected layout roles blocked"
    return RegionReadPlan(
        skip_vlm=False,
        reason=reason,
        tasks=tasks,
        stamp_regions_excluded=excluded_total,
        excluded_by_role=excluded_role,
        excluded_by_crs=excluded_crs,
        excluded_by_pii_clip=excluded_clip,
        excluded_by_geometry=excluded_geom,
        excluded_unknown_role=excluded_unknown,
    )


__all__ = [
    "RegionReadPlan",
    "RegionReadTask",
    "clip_pii_priors",
    "is_cloud_safe_layout_role",
    "is_stamp_like_region",
    "plan_region_reads",
    "priors_in_page_space",
    "subtract_aabb",
]
