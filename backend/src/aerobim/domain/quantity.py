"""Typed quantity and unit abstraction for AeroBIM.

Provides UCUM-aligned quantity values with SI normalization, enabling
reliable numeric comparisons across heterogeneous unit encodings
(e.g. "мм" vs "m" vs "3000 mm" vs "3.0 m").

References:
- UCUM (Unified Code for Units of Measure)
- ISO 80000 (Quantities and units)
- ISO 12006-3 (Building construction — Organization of information)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuantityValue:
    """A numeric value with explicit unit and optional SI-normalized form.

    Fields:
        value: The raw numeric value as extracted from source.
        unit: The raw unit string as extracted (may be Russian, informal, or UCUM).
        ucum_code: Canonical UCUM unit code if resolvable (None otherwise).
        dimension: Physical dimension category — "length", "area", "volume",
                   "angle", "mass", "time", "temperature", "dimensionless".
        si_value: Precomputed SI normalized value for comparison.
    """

    value: float
    unit: str
    ucum_code: str | None = None
    dimension: str | None = None
    si_value: float | None = None

    def __post_init__(self) -> None:
        # Defensive: strip and lowercase unit for consistency
        object.__setattr__(self, "unit", self.unit.strip())


# Mapping of common Russian AEC units to (UCUM code, SI conversion factor, dimension).
# Factor converts FROM the given unit TO the SI base unit.
_UNIT_REGISTRY: dict[str, tuple[str, float, str]] = {
    # Length
    "m": ("m", 1.0, "length"),
    "м": ("m", 1.0, "length"),
    "mm": ("mm", 0.001, "length"),
    "мм": ("mm", 0.001, "length"),
    "cm": ("cm", 0.01, "length"),
    "см": ("cm", 0.01, "length"),
    "km": ("km", 1000.0, "length"),
    "км": ("km", 1000.0, "length"),
    # Imperial length
    "ft": ("[ft_i]", 0.3048, "length"),
    "feet": ("[ft_i]", 0.3048, "length"),
    "foot": ("[ft_i]", 0.3048, "length"),
    "in": ("[in_i]", 0.0254, "length"),
    "inch": ("[in_i]", 0.0254, "length"),
    "inches": ("[in_i]", 0.0254, "length"),
    # Area
    "m2": ("m2", 1.0, "area"),
    "м2": ("m2", 1.0, "area"),
    "sqm": ("m2", 1.0, "area"),
    "sq.m": ("m2", 1.0, "area"),
    "m²": ("m2", 1.0, "area"),
    "м²": ("m2", 1.0, "area"),
    # Volume
    "m3": ("m3", 1.0, "volume"),
    "м3": ("m3", 1.0, "volume"),
    "cub.m": ("m3", 1.0, "volume"),
    "m³": ("m3", 1.0, "volume"),
    "м³": ("m3", 1.0, "volume"),
    # Angle
    "deg": ("deg", 1.0, "angle"),
    "degree": ("deg", 1.0, "angle"),
    "degrees": ("deg", 1.0, "angle"),
    "°": ("deg", 1.0, "angle"),
    "rad": ("rad", 1.0, "angle"),
    "radian": ("rad", 1.0, "angle"),
    "radians": ("rad", 1.0, "angle"),
    # Dimensionless / Percent
    "%": ("%", 1.0, "dimensionless"),
    "percent": ("%", 1.0, "dimensionless"),
    "ratio": ("1", 1.0, "dimensionless"),
    # Force / load (common AEC calc sheets) — SI newton
    "n": ("N", 1.0, "force"),
    "н": ("N", 1.0, "force"),
    "kn": ("kN", 1000.0, "force"),
    "кн": ("kN", 1000.0, "force"),
    "mn": ("MN", 1_000_000.0, "force"),
    "тс": ("tf", 9806.65, "force"),
    "tf": ("tf", 9806.65, "force"),
    # Pressure / distributed load
    "pa": ("Pa", 1.0, "pressure"),
    "kpa": ("kPa", 1000.0, "pressure"),
    "мпа": ("MPa", 1_000_000.0, "pressure"),
    "mpa": ("MPa", 1_000_000.0, "pressure"),
    "kn/m2": ("kN/m2", 1000.0, "pressure"),
    "кн/м2": ("kN/m2", 1000.0, "pressure"),
    "kn/m²": ("kN/m2", 1000.0, "pressure"),
}


def parse_quantity(value: float, unit: str) -> QuantityValue:
    """Parse a raw value+unit pair into a typed QuantityValue.

    Unknown units are accepted but will have ucum_code=None,
    dimension=None, and si_value=None.
    """
    normalized = unit.strip().lower()
    registry_entry = _UNIT_REGISTRY.get(normalized)
    if registry_entry is None:
        return QuantityValue(value=value, unit=unit)
    ucum_code, factor, dimension = registry_entry
    si_value = value * factor
    return QuantityValue(
        value=value,
        unit=unit,
        ucum_code=ucum_code,
        dimension=dimension,
        si_value=si_value,
    )


def si_compare(
    a: QuantityValue,
    b: QuantityValue,
    epsilon: float = 1e-6,
) -> bool:
    """Compare two QuantityValues for approximate equality in SI space.

    Returns True if both have si_value, dimensions match, and the absolute
    difference is <= epsilon. Returns False if either lacks si_value or
    dimensions differ (incompatible or unknown units).
    """
    if a.si_value is None or b.si_value is None:
        return False
    if a.dimension != b.dimension:
        return False
    return abs(a.si_value - b.si_value) <= epsilon
