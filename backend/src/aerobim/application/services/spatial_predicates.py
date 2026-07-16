"""Explicit spatial predicates — separate from IDS alphanumeric checks (W3.3).

IDS remains alphanumeric-only. Clearance / hard-clash predicates are evaluated
as a distinct module so claim boundaries stay honest (W78 IDS limits).
"""

from __future__ import annotations

from enum import StrEnum

from aerobim.domain.models import ClashResult, FindingCategory, Severity, ValidationIssue


class SpatialPredicateKind(StrEnum):
    HARD_CLASH = "hard_clash"
    CLEARANCE = "clearance"
    OPENING = "opening"


def issues_from_clash_results(
    results: tuple[ClashResult, ...] | list[ClashResult],
    *,
    affects_pass: bool = False,
) -> list[ValidationIssue]:
    """Map clash engine results to spatial-predicate issues (not IDS facets).

    Hard clashes are WARNING by default so ``summary.passed`` stays decoupled
    unless ``affects_pass`` (``AEROBIM_CLASH_AFFECTS_PASS``) is enabled — in that
    mode hard clashes become ERROR. Clearance clashes stay WARNING either way.
    A FAILED clash *capability* (engine crash) always blocks pass via sign-off policy.
    """
    issues: list[ValidationIssue] = []
    for clash in results:
        kind = (
            SpatialPredicateKind.CLEARANCE
            if clash.clash_type == "clearance"
            else SpatialPredicateKind.HARD_CLASH
        )
        if kind is SpatialPredicateKind.HARD_CLASH and affects_pass:
            severity = Severity.ERROR
        else:
            severity = Severity.WARNING
        issues.append(
            ValidationIssue(
                rule_id=f"SPATIAL-{kind.value.upper().replace('_', '-')}",
                severity=severity,
                message=(
                    f"Spatial predicate {kind.value}: elements "
                    f"{clash.element_a_guid} / {clash.element_b_guid} "
                    f"(distance={clash.distance:.4f} m)"
                ),
                element_guid=clash.element_a_guid,
                category=FindingCategory.SPATIAL,
            )
        )
    return issues
