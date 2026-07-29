"""Drawing-region type classifier (P1): heuristic, advisory, never a guess.

Competitive P1 (AIDOX): label a drawing region by type (stamp / specification /
explication / table / plan / section / facade / node / legend / dimension-chain /
schedule) from deterministic keyword + structure hints. Explicit ``UNKNOWN`` when
nothing matches OR the top match is ambiguous (a tie) — the classifier never guesses.

Honesty: ``heuristic_confidence`` is a coarse keyword-count score, NOT a calibrated
probability; the classification is ADVISORY (a hint for the expert / pipeline) and is
VERDICT-NEUTRAL — it does not set ``summary.passed`` (ADR-001). Terms: stamp — штамп;
specification — спецификация; explication — экспликация; dimension chain — размерная цепочка.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RegionType(StrEnum):
    STAMP = "stamp"
    SPECIFICATION = "specification"
    EXPLICATION = "explication"
    TABLE = "table"
    PLAN = "plan"
    SECTION = "section"
    FACADE = "facade"
    NODE = "node"
    LEGEND = "legend"
    DIMENSION_CHAIN = "dimension_chain"
    SCHEDULE = "schedule"
    UNKNOWN = "unknown"
    """No confident match, or an ambiguous tie — never a guess."""


# Deterministic Russian keyword hints per type. Matched with a LEFT word boundary so a
# stem cannot bleed mid-word (e.g. "механизм." never matches "изм."); collision-prone
# short stems (гип⊂гипсокартон, листов⊂листовая, generic марка) are dropped.
_KEYWORDS: dict[RegionType, tuple[str, ...]] = {
    RegionType.STAMP: ("стадия", "изм.", "разраб", "н.контр"),
    RegionType.SPECIFICATION: ("спецификация", "поз.", "наименование", "кол."),
    RegionType.EXPLICATION: ("экспликация", "помещен"),
    RegionType.LEGEND: ("условные обозначения", "легенда"),
    RegionType.NODE: ("узел",),
    RegionType.SECTION: ("разрез",),
    RegionType.FACADE: ("фасад",),
    RegionType.PLAN: ("план",),
    RegionType.SCHEDULE: ("график", "ведомость"),
}

# Keywords that must match as a WHOLE word (prevents e.g. "планировка" -> PLAN).
_WHOLE_WORD_KEYWORDS = frozenset({"план", "узел", "разрез", "фасад", "легенда", "график"})
_WORD_CHAR = r"[0-9A-Za-zА-Яа-яЁё]"


def _keyword_matches(keyword: str, lowered: str) -> bool:
    """Match keyword with a left word boundary (whole-word ones also need a right one)."""
    pattern = rf"(?<!{_WORD_CHAR}){re.escape(keyword)}"
    if keyword in _WHOLE_WORD_KEYWORDS:
        pattern += rf"(?!{_WORD_CHAR})"
    return re.search(pattern, lowered) is not None


@dataclass(frozen=True)
class RegionClassification:
    region_type: RegionType
    heuristic_confidence: float
    """Coarse keyword-count score in [0, 1] — NOT a calibrated probability."""
    matched_terms: tuple[str, ...]

    def is_known(self) -> bool:
        return self.region_type is not RegionType.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "region-classification",
            "note": (
                "heuristic keyword classifier; heuristic_confidence is NOT a calibrated "
                "probability; advisory hint, verdict-neutral (does NOT set summary.passed, ADR-001)"
            ),
            "region_type": self.region_type.value,
            "heuristic_confidence": self.heuristic_confidence,
            "matched_terms": list(self.matched_terms),
        }


def classify_region(
    text: str | None,
    *,
    has_table_structure: bool | None = None,
    numeric_ratio: float | None = None,
    min_numeric_ratio_for_dimension: float = 0.6,
) -> RegionClassification:
    """Classify a region by type (UNKNOWN on no match or an ambiguous tie).

    Keyword hits per type are counted; the strict maximum wins. A tie between distinct
    types -> UNKNOWN (never guess). ``has_table_structure`` yields TABLE only when no
    keyword matched; ``numeric_ratio`` yields DIMENSION_CHAIN only when dominant and no
    keyword matched. ``heuristic_confidence`` is an uncalibrated hint.
    """
    lowered = (text or "").lower()
    scores: dict[RegionType, int] = {}
    matched: dict[RegionType, tuple[str, ...]] = {}
    for region_type, keywords in _KEYWORDS.items():
        hits = tuple(kw for kw in keywords if _keyword_matches(kw, lowered))
        if hits:
            scores[region_type] = len(hits)
            matched[region_type] = hits

    # Structure hints apply only when no keyword matched; both hints add scores
    # independently so a both-hints region falls through to the tie -> UNKNOWN path.
    if not scores:
        if has_table_structure:
            scores[RegionType.TABLE] = 1
            matched[RegionType.TABLE] = ("table-structure",)
        if numeric_ratio is not None and numeric_ratio >= min_numeric_ratio_for_dimension:
            scores[RegionType.DIMENSION_CHAIN] = 1
            matched[RegionType.DIMENSION_CHAIN] = (
                f"numeric_ratio>={min_numeric_ratio_for_dimension}",
            )

    if not scores:
        return RegionClassification(RegionType.UNKNOWN, 0.0, ())

    top = max(scores.values())
    winners = sorted((t for t, s in scores.items() if s == top), key=lambda t: t.value)
    if len(winners) > 1:
        # Ambiguous — do not guess. Record the tied candidates for the expert.
        tied = tuple(f"{t.value}:{'|'.join(matched[t])}" for t in winners)
        return RegionClassification(RegionType.UNKNOWN, 0.0, tied)

    winner = winners[0]
    confidence = min(1.0, 0.4 + 0.2 * top)
    return RegionClassification(winner, confidence, matched[winner])


__all__ = [
    "RegionClassification",
    "RegionType",
    "classify_region",
]
