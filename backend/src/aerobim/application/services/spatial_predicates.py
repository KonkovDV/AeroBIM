"""Explicit spatial predicates — separate from IDS alphanumeric checks (W3.3).

IDS remains alphanumeric-only. Clearance / hard-clash predicates are evaluated
as a distinct module so claim boundaries stay honest (W78 IDS limits).
"""

from __future__ import annotations

from enum import StrEnum

from aerobim.domain.clash_triage import ClashTriageConfig, triage_clash_results
from aerobim.domain.models import ClashResult, FindingCategory, Severity, ValidationIssue


class SpatialPredicateKind(StrEnum):
    HARD_CLASH = "hard_clash"
    CLEARANCE = "clearance"
    OPENING = "opening"


def issues_from_clash_results(
    results: tuple[ClashResult, ...] | list[ClashResult],
    *,
    affects_pass: bool = False,
    triage_config: ClashTriageConfig | None = None,
) -> list[ValidationIssue]:
    """Map clash engine results to spatial-predicate issues (not IDS facets).

    Hard clashes are WARNING by default so ``summary.passed`` stays decoupled
    unless ``affects_pass`` (``AEROBIM_CLASH_AFFECTS_PASS``) is enabled — in that
    mode hard clashes become ERROR. Clearance clashes stay WARNING either way.
    A FAILED clash *capability* (engine crash) always blocks pass via sign-off policy.

    Issues are emitted in deterministic triage order (band → severity metric →
    pair key) with symmetric duplicates merged; the advisory triage band travels
    in ``evidence_refs`` and never changes severity or ``summary.passed``.
    """
    triage = triage_clash_results(results, config=triage_config)
    issues: list[ValidationIssue] = []
    for item in triage.items:
        clash = item.clash
        kind = (
            SpatialPredicateKind.CLEARANCE
            if clash.clash_type == "clearance"
            else SpatialPredicateKind.HARD_CLASH
        )
        if kind is SpatialPredicateKind.HARD_CLASH and affects_pass:
            severity = Severity.ERROR
        else:
            severity = Severity.WARNING
        pair_a, pair_b = item.pair_key
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
                target_ref=f"{pair_a}|{pair_b}",
                source_id="clash",
                finding_id=f"clash-{clash.clash_type}-{pair_a}-{pair_b}",
                evidence_refs=(
                    clash.element_a_guid,
                    clash.element_b_guid,
                    f"triage:band={item.band.value}",
                    f"triage:rank={item.rank}",
                    f"triage:{item.rationale}",
                    f"triage:duplicates_merged={item.duplicates_merged}",
                ),
                origin="deterministic",
            )
        )
    return issues
