"""DeterminismGate — deterministic engine always wins over advisory AI.

See Mirhosseini et al. (BRI 2026) Accuracy–Flexibility trade-off and
AeroBIM Contour.DETERMINISTIC_VALIDATION ownership of summary.passed.
"""

from __future__ import annotations

from collections.abc import Sequence

from aerobim.domain.models import (
    DivergenceRecord,
    FindingCategory,
    Severity,
    ValidationIssue,
)


def _issue_key(issue: ValidationIssue) -> str:
    if issue.finding_id:
        return issue.finding_id
    guid = issue.element_guid or ""
    return f"{issue.rule_id}|{guid}|{issue.target_ref or ''}"


class DeterminismGate:
    """Reconcile engine vs advisory issue sets.

    - Engine issues are authoritative and returned unchanged.
    - Advisory issues that contradict engine severity/message → DivergenceRecord + WARNING.
    - Advisory-only findings are demoted to INFO and never become ERROR (non-blocking).
    """

    def reconcile(
        self,
        *,
        engine_issues: Sequence[ValidationIssue],
        advisory_issues: Sequence[ValidationIssue],
    ) -> tuple[tuple[ValidationIssue, ...], tuple[DivergenceRecord, ...]]:
        engine_by_key = {_issue_key(issue): issue for issue in engine_issues}
        merged: list[ValidationIssue] = list(engine_issues)
        divergences: list[DivergenceRecord] = []

        for advisory in advisory_issues:
            key = _issue_key(advisory)
            engine = engine_by_key.get(key)
            if engine is None:
                merged.append(
                    ValidationIssue(
                        rule_id=advisory.rule_id,
                        severity=Severity.INFO,
                        message=(
                            f"[advisory-only] {advisory.message} "
                            "(DeterminismGate: not confirmed by deterministic engine)"
                        ),
                        ifc_entity=advisory.ifc_entity,
                        category=advisory.category,
                        target_ref=advisory.target_ref,
                        element_guid=advisory.element_guid,
                        problem_zone=advisory.problem_zone,
                        finding_id=advisory.finding_id,
                        evidence_refs=advisory.evidence_refs,
                        source_id=advisory.source_id or "ai-advisory",
                        confidence=advisory.confidence,
                        origin="advisory",
                    )
                )
                divergences.append(
                    DivergenceRecord(
                        finding_key=key,
                        engine_verdict="absent",
                        advisory_verdict=f"{advisory.severity.value}:{advisory.message}",
                    )
                )
                continue

            if engine.severity != advisory.severity or (engine.message or "") != (
                advisory.message or ""
            ):
                divergences.append(
                    DivergenceRecord(
                        finding_key=key,
                        engine_verdict=f"{engine.severity.value}:{engine.message}",
                        advisory_verdict=f"{advisory.severity.value}:{advisory.message}",
                    )
                )
                merged.append(
                    ValidationIssue(
                        rule_id="AEROBIM-DETERMINISM-DIVERGENCE",
                        severity=Severity.WARNING,
                        message=(
                            f"Advisory AI diverged from deterministic engine on {key}; "
                            "engine verdict retained"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                        element_guid=engine.element_guid,
                        target_ref=engine.target_ref,
                        finding_id=f"divergence:{key}",
                        evidence_refs=engine.evidence_refs,
                        source_id="determinism-gate",
                        origin="deterministic",
                    )
                )

        return tuple(merged), tuple(divergences)
