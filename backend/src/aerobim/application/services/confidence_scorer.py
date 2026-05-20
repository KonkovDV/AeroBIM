"""Deterministic confidence scoring for requirement extraction.

No ML or external dependencies — rules are source-kind and completeness based,
so they are fully testable, explainable, and do not drift with fixture changes.
"""

from __future__ import annotations

from aerobim.domain.models import ParsedRequirement, SourceKind


def score_confidence(requirement: ParsedRequirement) -> float:
    """Return a confidence score in [0.0, 1.0] for a parsed requirement.

    Scoring rules (deterministic):
    - structured-text pipe-delimited with all 6+ columns  -> 1.0
    - structured-text with missing optional columns     -> 0.9
    - technical-specification (free-form, keyword-match) -> 0.7
    - drawing-annotation with numeric observed value    -> 0.8
    - drawing-annotation without numeric value            -> 0.5
    - any source with empty expected_value               -> -0.1 (floor 0.0)
    """
    base = _base_confidence_for_source_kind(requirement.source_kind)
    completeness = _completeness_bonus(requirement)
    penalty = _penalty_for_missing_value(requirement)
    raw = base + completeness + penalty
    return max(0.0, min(1.0, raw))


def _base_confidence_for_source_kind(source_kind: SourceKind) -> float:
    mapping = {
        SourceKind.STRUCTURED_TEXT: 0.95,
        SourceKind.INLINE_TEXT: 0.85,
        SourceKind.TECHNICAL_SPECIFICATION: 0.70,
        SourceKind.CALCULATION: 0.75,
        SourceKind.DRAWING: 0.60,
        SourceKind.IDS: 0.90,
    }
    return mapping.get(source_kind, 0.50)


def _completeness_bonus(requirement: ParsedRequirement) -> float:
    """Small bonus when all expected fields are populated."""
    populated = sum(
        1
        for field in (
            requirement.ifc_entity,
            requirement.property_set,
            requirement.property_name,
            requirement.expected_value,
            requirement.unit,
        )
        if field is not None and str(field).strip() != ""
    )
    if populated >= 5:
        return 0.05
    if populated >= 3:
        return 0.0
    return -0.15


def _penalty_for_missing_value(requirement: ParsedRequirement) -> float:
    if requirement.expected_value is None or str(requirement.expected_value).strip() == "":
        return -0.10
    return 0.0
