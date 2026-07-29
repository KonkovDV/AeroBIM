"""Deterministic 2D geometry core (P2, verdict-neutral, no new dependencies).

Competitive P2 from WAIVE: measure geometry (areas / lengths / intersections) over
already-extracted primitives, with explicit unit/coordinate/completeness checks. This is
the DOMAIN core; a DXF/vector-PDF file parser is a separate adapter behind a port (needs
a licensed library) and is intentionally NOT here.

Honesty (coverage/quality lesson): a measurement is trustworthy ONLY when the geometry is
complete AND the unit is known AND coordinates are finite; otherwise the ``Measurement``
carries an explicit status (INCOMPLETE / UNIT_UNKNOWN / INVALID), never a silent value that
reads as '0 violations'. The language model does NOT compute geometry — this is fully
deterministic. Verdict-neutral: does NOT set ``summary.passed`` (ADR-001).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

Point = tuple[float, float]


class GeometryStatus(StrEnum):
    OK = "ok"
    INCOMPLETE = "incomplete"
    """Too few vertices / open where a closed contour is required."""
    UNIT_UNKNOWN = "unit_unknown"
    """Numeric value computed but the unit is unknown — not a trustworthy real-world value."""
    INVALID = "invalid"
    """Non-finite (NaN/inf) coordinate — cannot measure."""


@dataclass(frozen=True)
class Polyline:
    points: tuple[Point, ...]
    closed: bool = False


@dataclass(frozen=True)
class GeometryDocument:
    polylines: tuple[Polyline, ...] = ()
    unit: str | None = None
    coordinate_system: str | None = None


@dataclass(frozen=True)
class Measurement:
    kind: str  # "area" | "length"
    value: float | None
    unit: str | None
    status: GeometryStatus
    reasons: tuple[str, ...] = ()

    def is_trustworthy(self) -> bool:
        return self.status is GeometryStatus.OK


def _finite(point: Point) -> bool:
    return math.isfinite(point[0]) and math.isfinite(point[1])


def _all_finite(points: tuple[Point, ...]) -> bool:
    return all(_finite(p) for p in points)


def _close(a: Point, b: Point, tol: float) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def is_closed_contour(polyline: Polyline, *, tol: float = 1e-6) -> bool:
    pts = polyline.points
    if polyline.closed:
        return len(pts) >= 3
    return len(pts) >= 4 and _close(pts[0], pts[-1], tol)


def _shoelace(ring: list[Point]) -> float:
    total = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def measure_polygon_area(
    polyline: Polyline, *, unit: str | None = None, tol: float = 1e-6
) -> Measurement:
    pts = polyline.points
    if not _all_finite(pts):
        return Measurement("area", None, unit, GeometryStatus.INVALID, ("non-finite coordinate",))
    ring = list(pts)
    if len(ring) >= 2 and _close(ring[0], ring[-1], tol):
        ring = ring[:-1]  # drop the duplicate closing vertex for the shoelace ring
    if len(ring) < 3:
        return Measurement(
            "area", None, unit, GeometryStatus.INCOMPLETE, ("fewer than 3 vertices",)
        )
    if not is_closed_contour(polyline, tol=tol):
        return Measurement(
            "area", None, unit, GeometryStatus.INCOMPLETE, ("open contour; area undefined",)
        )
    area = abs(_shoelace(ring))
    if unit is None:
        return Measurement(
            "area",
            area,
            None,
            GeometryStatus.UNIT_UNKNOWN,
            ("unit unknown; value not trustworthy",),
        )
    return Measurement("area", area, unit, GeometryStatus.OK)


def measure_polyline_length(polyline: Polyline, *, unit: str | None = None) -> Measurement:
    pts = polyline.points
    if not _all_finite(pts):
        return Measurement("length", None, unit, GeometryStatus.INVALID, ("non-finite coordinate",))
    if len(pts) < 2:
        return Measurement(
            "length", None, unit, GeometryStatus.INCOMPLETE, ("fewer than 2 vertices",)
        )
    segments = list(zip(pts, pts[1:], strict=False))
    if polyline.closed and len(pts) >= 3:
        segments.append((pts[-1], pts[0]))
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segments)
    if unit is None:
        return Measurement(
            "length",
            length,
            None,
            GeometryStatus.UNIT_UNKNOWN,
            ("unit unknown; value not trustworthy",),
        )
    return Measurement("length", length, unit, GeometryStatus.OK)


def _orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
    """True if segment p1p2 intersects p3p4 (proper crossing or collinear touch)."""
    if not all(_finite(p) for p in (p1, p2, p3, p4)):
        return False
    d1, d2 = _orient(p3, p4, p1), _orient(p3, p4, p2)
    d3, d4 = _orient(p1, p2, p3), _orient(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    if d1 == 0 and _on_segment(p3, p4, p1):
        return True
    if d2 == 0 and _on_segment(p3, p4, p2):
        return True
    if d3 == 0 and _on_segment(p1, p2, p3):
        return True
    return d4 == 0 and _on_segment(p1, p2, p4)


def _segments(polyline: Polyline) -> list[tuple[Point, Point]]:
    pts = polyline.points
    segs = list(zip(pts, pts[1:], strict=False))
    if polyline.closed and len(pts) >= 3:
        segs.append((pts[-1], pts[0]))
    return segs


def polylines_intersect(a: Polyline, b: Polyline) -> bool:
    """True if any segment of ``a`` intersects any segment of ``b`` (deterministic)."""
    for a1, a2 in _segments(a):
        for b1, b2 in _segments(b):
            if segments_intersect(a1, a2, b1, b2):
                return True
    return False


def validate_geometry_document(doc: GeometryDocument) -> tuple[GeometryStatus, tuple[str, ...]]:
    """Pre-gate: geometry is measurable only with primitives + known unit + finite coords."""
    if not doc.polylines:
        return GeometryStatus.INCOMPLETE, ("no geometry primitives",)
    for polyline in doc.polylines:
        if not _all_finite(polyline.points):
            return GeometryStatus.INVALID, ("non-finite coordinate in a primitive",)
    if doc.unit is None or not doc.unit.strip():
        return GeometryStatus.UNIT_UNKNOWN, ("document unit unknown",)
    return GeometryStatus.OK, ()


__all__ = [
    "GeometryDocument",
    "GeometryStatus",
    "Measurement",
    "Point",
    "Polyline",
    "is_closed_contour",
    "measure_polygon_area",
    "measure_polyline_length",
    "polylines_intersect",
    "segments_intersect",
    "validate_geometry_document",
]
