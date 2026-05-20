"""Tests for typed quantity and unit abstraction."""

from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.quantity import parse_quantity, si_compare


class ParseQuantityTests(unittest.TestCase):
    def test_meter_identity(self) -> None:
        q = parse_quantity(3.0, "m")
        self.assertEqual(q.value, 3.0)
        self.assertEqual(q.ucum_code, "m")
        self.assertEqual(q.dimension, "length")
        self.assertEqual(q.si_value, 3.0)

    def test_russian_millimeter(self) -> None:
        q = parse_quantity(3000.0, "мм")
        self.assertEqual(q.ucum_code, "mm")
        self.assertEqual(q.dimension, "length")
        self.assertEqual(q.si_value, 3.0)

    def test_area_square_meter(self) -> None:
        q = parse_quantity(50.0, "m2")
        self.assertEqual(q.ucum_code, "m2")
        self.assertEqual(q.dimension, "area")
        self.assertEqual(q.si_value, 50.0)

    def test_russian_area(self) -> None:
        q = parse_quantity(50.0, "м²")
        self.assertEqual(q.ucum_code, "m2")
        self.assertEqual(q.dimension, "area")

    def test_volume(self) -> None:
        q = parse_quantity(120.0, "m3")
        self.assertEqual(q.ucum_code, "m3")
        self.assertEqual(q.dimension, "volume")
        self.assertEqual(q.si_value, 120.0)

    def test_unknown_unit_returns_none_meta(self) -> None:
        q = parse_quantity(42.0, "unknown-unit")
        self.assertIsNone(q.ucum_code)
        self.assertIsNone(q.dimension)
        self.assertIsNone(q.si_value)


class SiCompareTests(unittest.TestCase):
    def test_same_unit_equal(self) -> None:
        a = parse_quantity(3.0, "m")
        b = parse_quantity(3.0, "m")
        self.assertTrue(si_compare(a, b))

    def test_mm_vs_m_equal(self) -> None:
        a = parse_quantity(3000.0, "мм")
        b = parse_quantity(3.0, "m")
        self.assertTrue(si_compare(a, b, epsilon=0.001))

    def test_mm_vs_m_not_equal(self) -> None:
        a = parse_quantity(3001.0, "мм")
        b = parse_quantity(3.0, "m")
        self.assertFalse(si_compare(a, b, epsilon=0.0001))

    def test_incompatible_units_return_false(self) -> None:
        a = parse_quantity(3.0, "m")
        b = parse_quantity(3.0, "m2")
        self.assertFalse(si_compare(a, b))

    def test_unknown_units_return_false(self) -> None:
        a = parse_quantity(3.0, "foo")
        b = parse_quantity(3.0, "bar")
        self.assertFalse(si_compare(a, b))


class QuantityValueImmutabilityTests(unittest.TestCase):
    def test_frozen_dataclass(self) -> None:
        q = parse_quantity(1.0, "m")
        with self.assertRaises(FrozenInstanceError):
            q.value = 2.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
