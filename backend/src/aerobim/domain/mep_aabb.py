"""MEP AABB broadphase helpers — candidate filter only (NOT geometry-verified clash).

Industry alignment (IfcOpenShell Geometry Tree / Solibri / OSArch 2026):
axis-aligned bounding-box overlap is a broadphase prefilter. It does **not** prove
intersection, clearance violation, or product MEP clash. Analyze path must keep
``geometry_verified=False`` when mapping findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from aerobim.domain.mep import MepSystemGraph


def _pair_key(system_a: str, system_b: str) -> tuple[str, str]:
    left, right = sorted((system_a.strip(), system_b.strip()), key=str.casefold)
    return left, right


AabbFilterStatus = Literal["applied", "unavailable", "skipped"]


@dataclass(frozen=True)
class AxisAlignedBox3d:
    """World-axis AABB; coordinates in meters (IfcOpenShell convention)."""

    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    def __post_init__(self) -> None:
        if self.xmax < self.xmin or self.ymax < self.ymin or self.zmax < self.zmin:
            raise ValueError("AABB max must be >= min on each axis")


@dataclass(frozen=True)
class AabbFilterResult:
    """Outcome of optional AABB candidate filtering for matrix pairs."""

    status: AabbFilterStatus
    pairs: frozenset[tuple[str, str]]
    reason: str
    boxes_built: int = 0
    pairs_before: int = 0
    pairs_after: int = 0

    @property
    def evidence_token(self) -> str:
        return f"aabb_filter:{self.status}"


def aabb_overlap(a: AxisAlignedBox3d, b: AxisAlignedBox3d, *, eps: float = 0.0) -> bool:
    """True when AABBs overlap or touch within ``eps`` (meters)."""

    return not (
        a.xmax + eps < b.xmin
        or b.xmax + eps < a.xmin
        or a.ymax + eps < b.ymin
        or b.ymax + eps < a.ymin
        or a.zmax + eps < b.zmin
        or b.zmax + eps < a.zmin
    )


def union_aabb(
    boxes: tuple[AxisAlignedBox3d, ...] | list[AxisAlignedBox3d],
) -> AxisAlignedBox3d | None:
    if not boxes:
        return None
    xmin = min(box.xmin for box in boxes)
    ymin = min(box.ymin for box in boxes)
    zmin = min(box.zmin for box in boxes)
    xmax = max(box.xmax for box in boxes)
    ymax = max(box.ymax for box in boxes)
    zmax = max(box.zmax for box in boxes)
    return AxisAlignedBox3d(xmin, ymin, zmin, xmax, ymax, zmax)


def filter_pairs_by_aabb(
    pairs: set[tuple[str, str]] | frozenset[tuple[str, str]] | list[tuple[str, str]],
    system_boxes: dict[str, AxisAlignedBox3d],
    *,
    eps: float = 0.0,
) -> frozenset[tuple[str, str]]:
    """Keep undirected system pairs whose union AABBs overlap."""

    kept: set[tuple[str, str]] = set()
    for left, right in pairs:
        key = _pair_key(left, right)
        box_a = system_boxes.get(key[0])
        box_b = system_boxes.get(key[1])
        if box_a is None or box_b is None:
            continue
        if aabb_overlap(box_a, box_b, eps=eps):
            kept.add(key)
    return frozenset(kept)


def skipped_aabb_result(*, reason: str = "AABB filter not configured") -> AabbFilterResult:
    return AabbFilterResult(status="skipped", pairs=frozenset(), reason=reason)


def unavailable_aabb_result(*, reason: str, pairs_before: int = 0) -> AabbFilterResult:
    return AabbFilterResult(
        status="unavailable",
        pairs=frozenset(),
        reason=reason,
        pairs_before=pairs_before,
        pairs_after=0,
    )


def applied_aabb_result(
    pairs: frozenset[tuple[str, str]],
    *,
    boxes_built: int,
    pairs_before: int,
    reason: str = "AABB broadphase only — not geometry-verified (RT-003)",
) -> AabbFilterResult:
    return AabbFilterResult(
        status="applied",
        pairs=pairs,
        reason=reason,
        boxes_built=boxes_built,
        pairs_before=pairs_before,
        pairs_after=len(pairs),
    )


class MepAabbPairFilter(Protocol):
    """Optional port: broadphase system-pair candidates from AABB overlap."""

    def filter_pairs(self, graph: MepSystemGraph) -> AabbFilterResult: ...


__all__ = [
    "AabbFilterResult",
    "AabbFilterStatus",
    "AxisAlignedBox3d",
    "MepAabbPairFilter",
    "aabb_overlap",
    "applied_aabb_result",
    "filter_pairs_by_aabb",
    "skipped_aabb_result",
    "unavailable_aabb_result",
    "union_aabb",
]
