"""Typed quantity and unit abstraction for AeroBIM.

Provides UCUM-aligned quantity values with SI normalization, enabling
reliable numeric comparisons across heterogeneous unit encodings
(e.g. "мм" vs "m" vs "3000 mm" vs "3.0 m").

References:
- UCUM (Unified Code for Units of Measure)
- ISO 80000 (Quantities and units)
"""

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass

_GROUPING_SPACES = (
    "\u00a0",  # NBSP
    "\u202f",  # narrow NBSP
    "\u2009",  # thin space
    "\u2007",  # figure space
)

_NUMERIC_CHARS = frozenset("0123456789+-., ") | frozenset(_GROUPING_SPACES)


def looks_like_numeric_token(raw: str | None) -> bool:
    """True when the token is digit/separator-only (RU grouping included)."""
    if raw is None:
        return False
    text = unicodedata.normalize("NFKC", raw).strip()
    if not text or not any(char.isdigit() for char in text):
        return False
    return all(char in _NUMERIC_CHARS for char in text)


def parse_localized_number(raw: str | None) -> float | None:
    """Parse RU/EU/US grouped decimals without guessing ambiguous tokens.

    Accepts ``1 254,30``, NBSP grouping, ``1.254,30`` (dot thousands + comma
    decimal), and ``1,254.30`` (US). Rejects ``1.254`` (one-digit integer +
    three fraction digits: thousands vs decimal). ``10.005`` stays a decimal.
    """
    if raw is None:
        return None
    text = unicodedata.normalize("NFKC", raw).strip()
    if not text:
        return None
    for space in _GROUPING_SPACES:
        text = text.replace(space, " ")
    text = " ".join(text.split())
    if any(char.isalpha() for char in text) or not any(char.isdigit() for char in text):
        return None

    sign = 1.0
    if text[0] in "+-":
        sign = -1.0 if text[0] == "-" else 1.0
        text = text[1:].lstrip()
        if not text:
            return None

    if " " in text:
        joined = _join_space_thousands(text)
        if joined is None:
            return None
        text = joined

    parsed = _parse_comma_dot_body(text)
    if parsed is None:
        return None
    return sign * parsed


def _valid_thousand_chunks(chunks: list[str]) -> bool:
    if not chunks or not chunks[0].isdigit() or not (1 <= len(chunks[0]) <= 3):
        return False
    return all(chunk.isdigit() and len(chunk) == 3 for chunk in chunks[1:])


def _join_space_thousands(text: str) -> str | None:
    parts = text.split(" ")
    if len(parts) < 2:
        return None
    last = parts[-1]
    decimal_sep = None
    if "," in last and "." in last:
        return None
    if last.count(",") == 1 and "." not in last:
        decimal_sep = ","
    elif last.count(".") == 1 and "," not in last:
        decimal_sep = "."
    elif "," in last or "." in last:
        return None
    if decimal_sep is None:
        chunks = parts
        if not _valid_thousand_chunks(chunks):
            return None
        return "".join(chunks)
    int_last, frac = last.split(decimal_sep, 1)
    chunks = [*parts[:-1], int_last]
    if not frac.isdigit() or not _valid_thousand_chunks(chunks):
        return None
    return f"{''.join(chunks)}{decimal_sep}{frac}"


def _parse_comma_dot_body(body: str) -> float | None:
    if not body or any(char not in "0123456789.," for char in body):
        return None
    last_comma = body.rfind(",")
    last_dot = body.rfind(".")
    if last_comma != -1 and last_dot != -1:
        if last_comma > last_dot:
            return _split_thousands_and_decimal(body, thousands=".", decimal=",")
        return _split_thousands_and_decimal(body, thousands=",", decimal=".")
    if last_comma != -1:
        if body.count(",") == 1:
            left, right = body.split(",", 1)
            if left.isdigit() and right.isdigit():
                return float(f"{left}.{right}")
            return None
        return _integer_thousands(body, ",")
    if last_dot != -1:
        if body.count(".") == 1:
            left, right = body.split(".", 1)
            if not left.isdigit() or not right.isdigit():
                return None
            if left[0] != "0" and len(left) == 1 and len(right) == 3:
                return None
            return float(f"{left}.{right}")
        return _integer_thousands(body, ".")
    if body.isdigit():
        return float(body)
    return None


def _split_thousands_and_decimal(body: str, *, thousands: str, decimal: str) -> float | None:
    integer, frac = body.rsplit(decimal, 1)
    if not frac.isdigit():
        return None
    if thousands in integer:
        chunks = integer.split(thousands)
        if not _valid_thousand_chunks(chunks):
            return None
        digits = "".join(chunks)
    else:
        digits = integer
    if not digits.isdigit():
        return None
    return float(f"{digits}.{frac}")


def _integer_thousands(body: str, separator: str) -> float | None:
    chunks = body.split(separator)
    if not _valid_thousand_chunks(chunks):
        return None
    return float("".join(chunks))


def normalize_unit_token(unit: str | None) -> str:
    """NFKC-normalize a unit token so «м²» and «м2» compare equal.

    Superscript two (U+00B2) and compatibility superscripts (U+2072) fold to
    ASCII ``2``. Case is preserved so SI prefixes such as ``Mm`` vs ``mm`` are
    not collapsed. Registry lookup may still try a folded Cyrillic alias.
    """
    if not unit:
        return ""
    return unicodedata.normalize("NFKC", unit.strip())


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


# Case-sensitive SI / UCUM symbols. Latin prefixes are never folded.
_SI_SYMBOLS: dict[str, tuple[str, float, str]] = {
    "m": ("m", 1.0, "length"),
    "mm": ("mm", 0.001, "length"),
    "cm": ("cm", 0.01, "length"),
    "km": ("km", 1000.0, "length"),
    "ft": ("[ft_i]", 0.3048, "length"),
    "in": ("[in_i]", 0.0254, "length"),
    "m2": ("m2", 1.0, "area"),
    "sqm": ("m2", 1.0, "area"),
    "sq.m": ("m2", 1.0, "area"),
    "m²": ("m2", 1.0, "area"),
    "m3": ("m3", 1.0, "volume"),
    "cub.m": ("m3", 1.0, "volume"),
    "m³": ("m3", 1.0, "volume"),
    "deg": ("deg", math.pi / 180.0, "angle"),
    "°": ("deg", math.pi / 180.0, "angle"),
    "rad": ("rad", 1.0, "angle"),
    "%": ("%", 0.01, "dimensionless"),
    "ratio": ("1", 1.0, "dimensionless"),
    "N": ("N", 1.0, "force"),
    "mN": ("mN", 0.001, "force"),
    "kN": ("kN", 1000.0, "force"),
    "MN": ("MN", 1_000_000.0, "force"),
    "tf": ("tf", 9806.65, "force"),
    "Pa": ("Pa", 1.0, "pressure"),
    "mPa": ("mPa", 0.001, "pressure"),
    "kPa": ("kPa", 1000.0, "pressure"),
    "MPa": ("MPa", 1_000_000.0, "pressure"),
    "kN/m2": ("kN/m2", 1000.0, "pressure"),
    "kN/m²": ("kN/m2", 1000.0, "pressure"),
}

# Human / Cyrillic aliases. Folded lookup never maps milli ↔ mega SI symbols.
_UNIT_ALIASES: dict[str, str] = {
    "м": "m",
    "мм": "mm",
    "см": "cm",
    "км": "km",
    "feet": "ft",
    "foot": "ft",
    "inch": "in",
    "inches": "in",
    "м2": "m2",
    "м²": "m2",
    "м3": "m3",
    "м³": "m3",
    "degree": "deg",
    "degrees": "deg",
    "radian": "rad",
    "radians": "rad",
    "percent": "%",
    "n": "N",
    "н": "N",
    "kn": "kN",
    "кн": "kN",
    "тс": "tf",
    "pa": "Pa",
    "kpa": "kPa",
    "мпа": "MPa",
    "кн/м2": "kN/m2",
}


def _registry_entry(unit: str) -> tuple[str, float, str] | None:
    """Look up a unit without collapsing distinct SI prefixes.

    Exact SI symbols are tried first. Folded aliases cover Cyrillic and English
    spellings. Latin milli/mega pairs (``mN``/``MN``, ``mPa``/``MPa``, ``mm``/``Mm``)
    stay unknown unless the exact symbol is registered.
    """
    normalized = normalize_unit_token(unit)
    if not normalized:
        return None
    direct = _SI_SYMBOLS.get(normalized)
    if direct is not None:
        return direct
    alias = _UNIT_ALIASES.get(normalized) or _UNIT_ALIASES.get(normalized.lower())
    if alias is None:
        return None
    return _SI_SYMBOLS.get(alias)


def parse_quantity(value: float, unit: str) -> QuantityValue:
    """Parse a raw value+unit pair into a typed QuantityValue.

    Unknown units are accepted but will have ucum_code=None,
    dimension=None, and si_value=None.
    """
    registry_entry = _registry_entry(unit)
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
