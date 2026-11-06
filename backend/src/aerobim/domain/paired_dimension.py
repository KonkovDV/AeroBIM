"""A paired size on a drawing is not one scalar measurement.

A chain such as ``500×300`` names two sides. A thickness, width, height or
length rule must not take the first number and call it the opening. This is
not a product-accuracy claim and it does not write ``summary.passed``.
"""

from __future__ import annotations

import re

# Latin x, Cyrillic ha, and the multiplication sign. An asterisk is a grille
# size (``П300*300``) and is not this pattern.
_PAIRED_DIMENSION = re.compile(
    r"\d+(?:[.,]\d+)?\s*[xх×]\s*\d+(?:[.,]\d+)?",
    re.IGNORECASE,
)


def is_paired_dimension(text: str) -> bool:
    """True when the line states two sides of one size."""

    return _PAIRED_DIMENSION.search(text or "") is not None


def writes_summary_passed() -> bool:
    return False


__all__ = ["is_paired_dimension", "writes_summary_passed"]
