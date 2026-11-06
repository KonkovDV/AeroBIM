"""A paired size on a drawing is not one scalar measurement.

A chain such as ``500×300`` names two sides. A thickness, width, height or
length rule must not take either side and call it the opening. A different
number on the same line, such as a thickness written beside the opening, is
still a measurement. This is not a product-accuracy claim and it does not
write ``summary.passed``.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# Latin x, Cyrillic ha, and the multiplication sign. An asterisk is a grille
# size (``П300*300``) and is not this pattern. The mark must not sit inside a
# word: ``max`` is not ``m a x``. A unit may sit on either side
# (``500 mm x 300 mm``); ``mm`` is listed before ``m`` so the longer token wins.
_SIDE_UNIT = r"mm|мм|cm|см|m2|м2|m²|м²|m|м"
_PAIR_MARK = r"(?<![A-Za-zА-Яа-яЁё])[xх×](?![A-Za-zА-Яа-яЁё])"
_PAIRED_DIMENSION = re.compile(
    rf"\d+(?:[.,]\d+)?(?:\s*(?:{_SIDE_UNIT}))?\s*{_PAIR_MARK}\s*"
    rf"\d+(?:[.,]\d+)?(?:\s*(?:{_SIDE_UNIT}))?",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _number_key(value: str) -> str:
    """One key for ``500``, ``500.0`` and ``500,0``. A non-number stays as written."""

    text = (value or "").replace(",", ".").strip()
    if not text:
        return ""
    try:
        quantized = format(Decimal(text), "f")
    except InvalidOperation:
        return text
    if "." in quantized:
        quantized = quantized.rstrip("0").rstrip(".")
    return quantized


def paired_side_values(text: str) -> frozenset[str]:
    """Decimal keys of each side in every paired size on the line."""

    found: set[str] = set()
    for match in _PAIRED_DIMENSION.finditer(text or ""):
        for number in _NUMBER.findall(match.group(0)):
            found.add(_number_key(number))
    return frozenset(found)


def is_paired_dimension(text: str) -> bool:
    """True when the line states two sides of one size."""

    return bool(paired_side_values(text))


def value_is_paired_side(text: str, value: str) -> bool:
    """True when this scalar is one side of a paired size, not a separate measure."""

    sides = paired_side_values(text)
    if not sides:
        return False
    return _number_key(value) in sides


def writes_summary_passed() -> bool:
    return False


__all__ = [
    "is_paired_dimension",
    "paired_side_values",
    "value_is_paired_side",
    "writes_summary_passed",
]
