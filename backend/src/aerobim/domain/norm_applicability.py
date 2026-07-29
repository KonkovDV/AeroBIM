"""Norm-rule applicability + exceptions matcher (P3/normative, verdict-neutral).

Competitive P0 from NormaChecker: a rule must carry an explicit applicability scope
(building type / discipline / stage) and exceptions, and only APPLY when the project
context provably matches. This module is the pure decision predicate.

Fail-safe honesty (coverage-map lesson): when the context is insufficient to decide a
constrained dimension, the result is ``UNKNOWN`` — the rule is NEITHER silently applied
NOR silently skipped; it goes to the expert. ``APPLICABLE`` is returned only when every
constrained dimension provably matches AND no exception can apply.

Domain-pure; VERDICT-NEUTRAL — it decides whether a rule is IN SCOPE for evaluation, not
whether the model passes; the deterministic engine still owns ``summary.passed`` (ADR-001).
Terms: applicability — область применения; exception — исключение; stage — стадия.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ApplicabilityStatus(StrEnum):
    APPLICABLE = "applicable"
    """Context provably matches the scope and no exception can apply — evaluate the rule."""
    NOT_APPLICABLE = "not_applicable"
    """Context provably outside the scope — skip (this is NOT 'passed')."""
    EXCLUDED = "excluded"
    """An exception provably matches — the rule is excepted for this context."""
    UNKNOWN = "unknown"
    """Insufficient context to decide — expert required (never a silent apply/skip)."""


@dataclass(frozen=True)
class ApplicabilityException:
    building_types: tuple[str, ...] = ()
    disciplines: tuple[str, ...] = ()
    stages: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class RuleApplicability:
    """Empty tuple on a dimension means 'any' (that dimension is unconstrained)."""

    building_types: tuple[str, ...] = ()
    disciplines: tuple[str, ...] = ()
    stages: tuple[str, ...] = ()
    exceptions: tuple[ApplicabilityException, ...] = ()


@dataclass(frozen=True)
class ProjectContext:
    building_type: str | None = None
    discipline: str | None = None
    stage: str | None = None


@dataclass(frozen=True)
class ApplicabilityResult:
    status: ApplicabilityStatus
    reasons: tuple[str, ...] = ()

    def should_evaluate(self) -> bool:
        """Only APPLICABLE rules may be auto-evaluated; all else defers to the expert/skip."""
        return self.status is ApplicabilityStatus.APPLICABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "norm-applicability",
            "note": (
                "decides if a rule is in scope for a project context; UNKNOWN on insufficient "
                "context (never a silent apply/skip); NOT_APPLICABLE is not 'passed'; "
                "verdict-neutral (does NOT set summary.passed, ADR-001)"
            ),
            "status": self.status.value,
            "reasons": list(self.reasons),
        }


# Per-dimension match outcome against a constrained set.
_MATCH = "match"
_MISMATCH = "mismatch"
_INDETERMINATE = "indeterminate"


def _match_dimension(allowed: tuple[str, ...], value: str | None) -> str:
    if not allowed:
        return _MATCH  # unconstrained dimension matches anything
    if value is None:
        return _INDETERMINATE  # constrained but context unknown -> cannot decide
    return _MATCH if value in allowed else _MISMATCH


def _exception_state(exception: ApplicabilityException, context: ProjectContext) -> str:
    """MATCH only if every constrained dim is known and in-set; MISMATCH on any known
    out-of-set dim; otherwise INDETERMINATE (cannot rule the exception out)."""
    states = (
        _match_dimension(exception.building_types, context.building_type),
        _match_dimension(exception.disciplines, context.discipline),
        _match_dimension(exception.stages, context.stage),
    )
    if _MISMATCH in states:
        return _MISMATCH
    if _INDETERMINATE in states:
        return _INDETERMINATE
    return _MATCH


def evaluate_applicability(
    applicability: RuleApplicability, context: ProjectContext
) -> ApplicabilityResult:
    """Decide whether a rule applies to a project context (fail-safe to UNKNOWN)."""
    base = (
        _match_dimension(applicability.building_types, context.building_type),
        _match_dimension(applicability.disciplines, context.discipline),
        _match_dimension(applicability.stages, context.stage),
    )
    if _MISMATCH in base:
        return ApplicabilityResult(
            ApplicabilityStatus.NOT_APPLICABLE, ("context outside rule applicability scope",)
        )
    if _INDETERMINATE in base:
        return ApplicabilityResult(
            ApplicabilityStatus.UNKNOWN,
            ("insufficient context to confirm applicability scope",),
        )

    # Base scope provably matches. An exception that provably matches excludes the rule;
    # an exception we cannot rule out (indeterminate) forces UNKNOWN.
    indeterminate_exception = False
    for exception in applicability.exceptions:
        state = _exception_state(exception, context)
        if state == _MATCH:
            reason = exception.reason or "exception matches context"
            return ApplicabilityResult(ApplicabilityStatus.EXCLUDED, (reason,))
        if state == _INDETERMINATE:
            indeterminate_exception = True
    if indeterminate_exception:
        return ApplicabilityResult(
            ApplicabilityStatus.UNKNOWN,
            ("cannot rule out an exception with the given context",),
        )
    return ApplicabilityResult(
        ApplicabilityStatus.APPLICABLE, ("context matches scope; no exception applies",)
    )


__all__ = [
    "ApplicabilityException",
    "ApplicabilityResult",
    "ApplicabilityStatus",
    "ProjectContext",
    "RuleApplicability",
    "evaluate_applicability",
]
