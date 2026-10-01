"""IDS compile draft and norm corpus passage types (advisory NLP contour)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdsCompileDraft:
    """Machine-drafted IDS 1.0 XML — advisory until human promotes to ids_path."""

    suggested_ids_xml: str
    rationale: str
    source_requirement_count: int
    advisory_only: bool = True
    confidence: float = 0.4
    rase_elements: tuple[str, ...] = ()
    """Aggregated R/A/S/E tags across compiled rules (I8b)."""
    rase_summary: str | None = None


@dataclass(frozen=True)
class NormPassage:
    """Retrieved norm excerpt with citation metadata."""

    passage_id: str
    title: str
    text: str
    source_path: str
    score: float
    clause_hint: str | None = None
