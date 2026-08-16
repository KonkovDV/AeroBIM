"""DeterminismGate — deterministic engine always wins over advisory AI.

See Mirhosseini et al. (BRI 2026) Accuracy–Flexibility trade-off and
AeroBIM Contour.DETERMINISTIC_VALIDATION ownership of summary.passed.

Wave J (2026-07-25) — atomic evidence grounding: advisory-only findings are
checked against the deterministic evidence universe (known element GUIDs /
target refs from engine issues, requirements, clash pairs, drawing
annotations). References unknown to the engine are stamped ``[ungrounded]``
(hallucinated-reference class — TACO EACL 2026 / Chain-of-Verification
practice: every advisory claim must bind to verifiable evidence). Grounding
never raises severity and never flips ``summary.passed``.

HD4-INV-02: advisory writers must not construct ``Severity.ERROR`` — that is a
construction convention plus this gate's INFO demotion, not a type isolation.
Deserialized issues keep the stored severity; integrity is the content-hash
(RTATOM-G11), not the type system.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

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


def build_evidence_universe(
    *,
    engine_issues: Sequence[ValidationIssue] = (),
    requirements: Iterable[object] = (),
    clash_results: Iterable[object] = (),
    drawing_annotations: Iterable[object] = (),
) -> frozenset[str]:
    """Collect entity tokens known to the deterministic contour.

    Tokens: engine issue element_guids/target_refs, requirement rule_ids and
    target_refs, clash pair GUIDs, drawing annotation target_refs. Used to
    ground advisory references — anything outside this set was never seen by
    the engine.
    """

    tokens: set[str] = set()
    for issue in engine_issues:
        if issue.element_guid:
            tokens.add(issue.element_guid)
        if issue.target_ref:
            tokens.add(issue.target_ref)
    for requirement in requirements:
        for attr in ("rule_id", "target_ref", "ifc_entity"):
            value = getattr(requirement, attr, None)
            if value:
                tokens.add(str(value))
    for clash in clash_results:
        for attr in ("element_a_guid", "element_b_guid"):
            value = getattr(clash, attr, None)
            if value:
                tokens.add(str(value))
    for annotation in drawing_annotations:
        value = getattr(annotation, "target_ref", None)
        if value:
            tokens.add(str(value))
    return frozenset(tokens)


def _grounding_state(
    issue: ValidationIssue,
    universe: frozenset[str],
) -> tuple[str, tuple[str, ...]]:
    """Classify advisory references: verified / unverified / no reference."""

    references = tuple(ref for ref in (issue.element_guid, issue.target_ref) if ref)
    if not references:
        return "no_verifiable_reference", ()
    unknown = tuple(ref for ref in references if ref not in universe)
    if unknown:
        return "unverified_reference", unknown
    return "verified_reference", ()


class DeterminismGate:
    """Reconcile engine vs advisory issue sets.

    - Engine issues are authoritative and returned unchanged.
    - Advisory issues that contradict engine severity/message → DivergenceRecord + WARNING.
    - Advisory-only findings are demoted to INFO and never become ERROR (non-blocking).
    - With an ``evidence_universe``: advisory-only references unknown to the
      engine are stamped ``[ungrounded]`` + ``grounding:unverified_reference``
      (never dropped — visible and flagged for HITL).
    """

    def reconcile(
        self,
        *,
        engine_issues: Sequence[ValidationIssue],
        advisory_issues: Sequence[ValidationIssue],
        evidence_universe: frozenset[str] | None = None,
    ) -> tuple[tuple[ValidationIssue, ...], tuple[DivergenceRecord, ...]]:
        engine_by_key = {_issue_key(issue): issue for issue in engine_issues}
        merged: list[ValidationIssue] = list(engine_issues)
        divergences: list[DivergenceRecord] = []

        for advisory in advisory_issues:
            key = _issue_key(advisory)
            engine = engine_by_key.get(key)
            if engine is None:
                message = (
                    f"[advisory-only] {advisory.message} "
                    "(DeterminismGate: not confirmed by deterministic engine)"
                )
                extra_refs: tuple[str, ...] = ()
                advisory_verdict = f"{advisory.severity.value}:{advisory.message}"
                if evidence_universe is not None:
                    state, unknown = _grounding_state(advisory, evidence_universe)
                    extra_refs = (f"grounding:{state}",)
                    if state == "unverified_reference":
                        message = (
                            f"[ungrounded] {message} — references unknown to the "
                            f"deterministic engine: {', '.join(unknown)}"
                        )
                        advisory_verdict = f"ungrounded:{advisory_verdict}"
                merged.append(
                    ValidationIssue(
                        rule_id=advisory.rule_id,
                        severity=Severity.INFO,
                        message=message,
                        ifc_entity=advisory.ifc_entity,
                        category=advisory.category,
                        target_ref=advisory.target_ref,
                        element_guid=advisory.element_guid,
                        problem_zone=advisory.problem_zone,
                        finding_id=advisory.finding_id,
                        evidence_refs=(*advisory.evidence_refs, *extra_refs),
                        source_id=advisory.source_id or "ai-advisory",
                        confidence=advisory.confidence,
                        origin="advisory",
                        remark=advisory.remark,
                    )
                )
                divergences.append(
                    DivergenceRecord(
                        finding_key=key,
                        engine_verdict="absent",
                        advisory_verdict=advisory_verdict,
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
