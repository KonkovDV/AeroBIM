"""Map findings onto CORENET-like gates and answer nature.

Schema / quality / regulatory is a report grouping, not a product-accuracy claim.
Deterministic rows are not scored as «точность >90%». Advisory origin is
probabilistic and never writes summary.passed (ADR-001).
"""

from __future__ import annotations

from aerobim.domain.findings import FindingPredicate, predicate_for_issue
from aerobim.domain.models import ValidationIssue
from aerobim.domain.remark_shape import ANSWER_NATURES, GATE_CLASSES

GateClass = str
AnswerNature = str

_SCHEMA_PREDICATES = frozenset({FindingPredicate.SCHEMA_GATE})
_QUALITY_PREDICATES = frozenset(
    {
        FindingPredicate.IDS_FACET,
        FindingPredicate.VERSION_MISMATCH,
        FindingPredicate.DRAWING_MEASURE,
        FindingPredicate.OTHER,
    }
)
_REGULATORY_PREDICATES = frozenset(
    {
        FindingPredicate.GEOMETRIC_CLASH,
        FindingPredicate.NORM_VIOLATION,
        FindingPredicate.CROSS_DOCUMENT,
    }
)


def classify_finding_gate(issue: ValidationIssue) -> tuple[GateClass, AnswerNature]:
    nature: AnswerNature = "probabilistic" if issue.origin == "advisory" else "deterministic"
    predicate = predicate_for_issue(issue)
    if predicate in _SCHEMA_PREDICATES:
        gate: GateClass = "schema"
    elif predicate in _REGULATORY_PREDICATES:
        gate = "regulatory"
    elif predicate in _QUALITY_PREDICATES:
        gate = "quality"
    else:
        gate = "quality"
    if gate not in GATE_CLASSES or nature not in ANSWER_NATURES:
        raise ValueError(f"invalid gate mapping {gate!r}/{nature!r}")
    return gate, nature


def stamp_finding_gate(issue: ValidationIssue) -> ValidationIssue:
    """Return a copy with gate_class and answer_nature filled."""

    from dataclasses import replace

    gate, nature = classify_finding_gate(issue)
    return replace(issue, gate_class=gate, answer_nature=nature)


__all__ = ["classify_finding_gate", "stamp_finding_gate"]
