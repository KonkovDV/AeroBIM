"""Deterministic geometry core: measurements + honest status (P2).

Trustworthy only when complete + unit known + finite; otherwise explicit
INCOMPLETE/UNIT_UNKNOWN/INVALID. LLM does not compute; verdict-neutral.
"""

from __future__ import annotations

import math
import unittest

from aerobim.domain.geometry import (
    GeometryDocument,
    GeometryStatus,
    Polyline,
    is_closed_contour,
    measure_polygon_area,
    measure_polyline_length,
    polylines_intersect,
    segments_intersect,
    validate_geometry_document,
)

_SQUARE = Polyline(points=((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)), closed=True)


class GeometryTests(unittest.TestCase):
    def test_area_of_unit_square(self) -> None:
        m = measure_polygon_area(_SQUARE, unit="mm")
        self.assertEqual(m.status, GeometryStatus.OK)
        self.assertAlmostEqual(m.value or 0.0, 1.0)
        self.assertTrue(m.is_trustworthy())

    def test_area_without_unit_is_unit_unknown(self) -> None:
        m = measure_polygon_area(_SQUARE)
        self.assertEqual(m.status, GeometryStatus.UNIT_UNKNOWN)
        self.assertAlmostEqual(m.value or 0.0, 1.0)  # value computed but flagged
        self.assertFalse(m.is_trustworthy())

    def test_area_open_contour_is_incomplete(self) -> None:
        m = measure_polygon_area(Polyline(points=((0.0, 0.0), (0.0, 1.0), (1.0, 1.0))), unit="mm")
        self.assertEqual(m.status, GeometryStatus.INCOMPLETE)
        self.assertIsNone(m.value)

    def test_area_too_few_vertices_is_incomplete(self) -> None:
        m = measure_polygon_area(Polyline(points=((0.0, 0.0), (1.0, 1.0)), closed=True), unit="mm")
        self.assertEqual(m.status, GeometryStatus.INCOMPLETE)

    def test_area_non_finite_is_invalid(self) -> None:
        m = measure_polygon_area(
            Polyline(points=((0.0, 0.0), (float("nan"), 1.0), (1.0, 1.0)), closed=True), unit="mm"
        )
        self.assertEqual(m.status, GeometryStatus.INVALID)

    def test_length_of_polyline(self) -> None:
        m = measure_polyline_length(Polyline(points=((0.0, 0.0), (0.0, 3.0))), unit="m")
        self.assertEqual(m.status, GeometryStatus.OK)
        self.assertAlmostEqual(m.value or 0.0, 3.0)

    def test_length_without_unit_is_unit_unknown(self) -> None:
        m = measure_polyline_length(Polyline(points=((0.0, 0.0), (0.0, 3.0))))
        self.assertEqual(m.status, GeometryStatus.UNIT_UNKNOWN)

    def test_length_too_few_vertices_is_incomplete(self) -> None:
        m = measure_polyline_length(Polyline(points=((0.0, 0.0),)), unit="m")
        self.assertEqual(m.status, GeometryStatus.INCOMPLETE)

    def test_length_non_finite_is_invalid(self) -> None:
        m = measure_polyline_length(Polyline(points=((0.0, 0.0), (math.inf, 1.0))), unit="m")
        self.assertEqual(m.status, GeometryStatus.INVALID)

    def test_segments_intersect_crossing(self) -> None:
        self.assertTrue(segments_intersect((0.0, 0.0), (2.0, 2.0), (0.0, 2.0), (2.0, 0.0)))

    def test_segments_do_not_intersect_parallel(self) -> None:
        self.assertFalse(segments_intersect((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)))

    def test_segments_intersect_non_finite_is_false(self) -> None:
        self.assertFalse(
            segments_intersect((0.0, 0.0), (float("nan"), 2.0), (0.0, 2.0), (2.0, 0.0))
        )

    def test_polylines_intersect(self) -> None:
        a = Polyline(points=((0.0, 0.0), (2.0, 2.0)))
        b = Polyline(points=((0.0, 2.0), (2.0, 0.0)))
        self.assertTrue(polylines_intersect(a, b))

    def test_polylines_disjoint(self) -> None:
        a = Polyline(points=((0.0, 0.0), (1.0, 0.0)))
        b = Polyline(points=((0.0, 5.0), (1.0, 5.0)))
        self.assertFalse(polylines_intersect(a, b))

    def test_is_closed_contour(self) -> None:
        self.assertTrue(
            is_closed_contour(Polyline(points=((0.0, 0.0), (1.0, 1.0), (2.0, 0.0)), closed=True))
        )
        self.assertTrue(
            is_closed_contour(Polyline(points=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0))))
        )
        self.assertFalse(is_closed_contour(Polyline(points=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0)))))

    def test_validate_geometry_document(self) -> None:
        self.assertEqual(
            validate_geometry_document(GeometryDocument())[0], GeometryStatus.INCOMPLETE
        )
        self.assertEqual(
            validate_geometry_document(GeometryDocument(polylines=(_SQUARE,)))[0],
            GeometryStatus.UNIT_UNKNOWN,
        )
        self.assertEqual(
            validate_geometry_document(GeometryDocument(polylines=(_SQUARE,), unit="mm"))[0],
            GeometryStatus.OK,
        )


if __name__ == "__main__":
    unittest.main()
