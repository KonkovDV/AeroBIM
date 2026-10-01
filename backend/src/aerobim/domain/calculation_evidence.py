"""Evidence-only calculation match outcomes (not independent solver correctness)."""

from __future__ import annotations

from enum import StrEnum


class CalculationEvidenceOutcome(StrEnum):
    """Result of сверка / provenance match — never implies solver correctness."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    SOURCE_MISSING = "SOURCE_MISSING"
    SOURCE_UNVERIFIED = "SOURCE_UNVERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    """Reserved for independent calculation_correctness — always this until a solver ships."""


CALCULATION_CORRECTNESS_CLAIM = "evidence_consistency_only"
CALCULATION_CORRECTNESS_REASON = "independent solver verification is not implemented"
FORBIDDEN_CALC_CLAIM_PHRASES = frozenset(
    {
        "calculation_correctness_verified",
        "independent calculation correctness verified",
        "solver verification passed",
        "расчётная корректность подтверждена",
    }
)


def independent_solver_not_implemented_payload() -> dict[str, object]:
    """Honesty payload when independent calculation correctness is requested."""

    return {
        "status": CalculationEvidenceOutcome.NOT_IMPLEMENTED.value.lower(),
        "claim": CALCULATION_CORRECTNESS_CLAIM,
        "reason": CALCULATION_CORRECTNESS_REASON,
        "affects_pass": True,
    }


__all__ = [
    "CALCULATION_CORRECTNESS_CLAIM",
    "CALCULATION_CORRECTNESS_REASON",
    "CalculationEvidenceOutcome",
    "FORBIDDEN_CALC_CLAIM_PHRASES",
    "independent_solver_not_implemented_payload",
]
