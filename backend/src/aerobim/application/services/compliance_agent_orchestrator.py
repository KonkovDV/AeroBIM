"""ComplianceAgentOrchestrator — ReAct-style tool orchestration over DI ports.

Deterministic planner (no LLM in v1): selects allowlisted tools from the request
shape, executes them, and emits advisory ValidationIssue records only.
DeterminismGate must reconcile these against the engine before persistence.

Literature: TUM/Iversen&Huang agentic ACC tool-calling; MCP4IFC tool registry;
Mirhosseini et al. BRI 2026 hybrid determinism ≻ LLM for sign-off.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from aerobim.domain.compliance_agent import AgentRunResult, AgentToolStep
from aerobim.domain.consistency import PackageManifest, claims_from_area_requirements
from aerobim.domain.models import (
    FindingCategory,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.domain.norm_assist import IdsCompileDraft, NormPassage
from aerobim.domain.ports import (
    ClashDetector,
    LoadEvidenceVerifier,
    LogicConsistencyAnalyzer,
    NormCorpusRetriever,
    QuantityConsistencyChecker,
    RequirementToIdsCompiler,
)

_ALLOWED_TOOLS = frozenset(
    {
        "retrieve_norms",
        "compile_ids_draft",
        "verify_loads",
        "analyze_logic",
        "check_quantities",
        "detect_clashes",
    }
)


class ComplianceAgentOrchestrator:
    """Application orchestrator: plan → tool-call → advisory findings.

    Hard invariants:
    - Only ``_ALLOWED_TOOLS`` may execute.
    - ``max_steps`` caps the loop (default 6).
    - Outputs are advisory; callers must pass them through DeterminismGate.
    """

    def __init__(
        self,
        *,
        norm_retriever: NormCorpusRetriever | None = None,
        ids_compiler: RequirementToIdsCompiler | None = None,
        load_verifier: LoadEvidenceVerifier | None = None,
        logic_analyzer: LogicConsistencyAnalyzer | None = None,
        quantity_checker: QuantityConsistencyChecker | None = None,
        clash_detector: ClashDetector | None = None,
        max_steps: int = 6,
    ) -> None:
        self._norm_retriever = norm_retriever
        self._ids_compiler = ids_compiler
        self._load_verifier = load_verifier
        self._logic_analyzer = logic_analyzer
        self._quantity_checker = quantity_checker
        self._clash_detector = clash_detector
        self._max_steps = max(1, max_steps)

    def run(self, request: ValidationRequest) -> AgentRunResult:
        plan = self._plan(request)
        capped = len(plan) > self._max_steps
        plan = plan[: self._max_steps]

        executed: list[AgentToolStep] = []
        advisory: list[ValidationIssue] = []
        passages: list[NormPassage] = []
        ids_draft: IdsCompileDraft | None = None

        handlers: dict[
            str,
            Callable[
                [ValidationRequest, AgentToolStep],
                tuple[
                    AgentToolStep,
                    list[ValidationIssue],
                    list[NormPassage],
                    IdsCompileDraft | None,
                ],
            ],
        ] = {
            "retrieve_norms": self._tool_retrieve_norms,
            "compile_ids_draft": self._tool_compile_ids,
            "verify_loads": self._tool_verify_loads,
            "analyze_logic": self._tool_analyze_logic,
            "check_quantities": self._tool_check_quantities,
            "detect_clashes": self._tool_detect_clashes,
        }

        for step in plan:
            if step.tool_name not in _ALLOWED_TOOLS:
                executed.append(
                    AgentToolStep(
                        tool_name=step.tool_name,
                        rationale=step.rationale,
                        arguments=step.arguments,
                        status="error",
                        detail="tool not in allowlist",
                    )
                )
                continue
            handler = handlers[step.tool_name]
            done, issues, more_passages, maybe_draft = handler(request, step)
            executed.append(done)
            advisory.extend(issues)
            passages.extend(more_passages)
            if maybe_draft is not None:
                ids_draft = maybe_draft

        if capped:
            advisory.append(
                ValidationIssue(
                    rule_id="AEROBIM-AGENT-CAP",
                    severity=Severity.INFO,
                    message=(f"Compliance agent plan truncated at max_steps={self._max_steps}"),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="compliance-agent",
                    confidence=1.0,
                )
            )

        return AgentRunResult(
            steps=tuple(executed),
            advisory_issues=tuple(advisory),
            norm_passages=tuple(passages),
            ids_draft=ids_draft,
            capped=capped,
        )

    def _plan(self, request: ValidationRequest) -> list[AgentToolStep]:
        steps: list[AgentToolStep] = []
        query = self._enrich_query(request)
        if query and self._norm_retriever is not None:
            steps.append(
                AgentToolStep(
                    tool_name="retrieve_norms",
                    rationale="Retrieve norm passages for package narrative context",
                    arguments={"query": query[:500]},
                )
            )
        if self._ids_compiler is not None and (
            request.requirement_source.text.strip()
            or request.requirement_source.path is not None
            or request.technical_spec_source is not None
        ):
            steps.append(
                AgentToolStep(
                    tool_name="compile_ids_draft",
                    rationale="Draft IDS from structured/technical requirements (advisory)",
                    arguments={},
                )
            )
        if request.calculation_source is not None and self._load_verifier is not None:
            steps.append(
                AgentToolStep(
                    tool_name="verify_loads",
                    rationale="Run load-table сверка on calculation source",
                    arguments={},
                )
            )
        if self._logic_analyzer is not None:
            steps.append(
                AgentToolStep(
                    tool_name="analyze_logic",
                    rationale="Check package logical consistency (PD/RD, sheets)",
                    arguments={},
                )
            )
        if self._quantity_checker is not None:
            steps.append(
                AgentToolStep(
                    tool_name="check_quantities",
                    rationale="Advisory IFC quantity сверка vs declared area/volume claims",
                    arguments={},
                )
            )
        if self._clash_detector is not None and request.ifc_path is not None:
            steps.append(
                AgentToolStep(
                    tool_name="detect_clashes",
                    rationale="Advisory generic clash probe (not MEP system-aware)",
                    arguments={},
                )
            )
        return steps

    def _enrich_query(self, request: ValidationRequest) -> str:
        chunks: list[str] = []
        for source in (
            request.technical_spec_source,
            request.requirement_source,
            request.calculation_source,
        ):
            if source is None:
                continue
            if source.text.strip():
                chunks.append(source.text.strip()[:400])
        if request.discipline:
            chunks.append(request.discipline)
        return " ".join(chunks)

    def _tool_retrieve_norms(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        del request
        assert self._norm_retriever is not None
        query = step.arguments.get("query", "")
        try:
            hits = self._norm_retriever.retrieve(query, top_k=5)
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-NORMS",
                        severity=Severity.INFO,
                        message=f"Norm retrieve failed: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        issues: list[ValidationIssue] = []
        if hits:
            top = hits[0]
            evidence_label = Path(top.source_path).name or "norm-corpus"
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-AGENT-NORM-HIT",
                    severity=Severity.INFO,
                    message=(
                        f"[advisory] Norm corpus hit: {top.title} "
                        f"(score={top.score:.2f}) @ {evidence_label} [unapproved/sample]"
                    ),
                    category=FindingCategory.CROSS_DOCUMENT,
                    source_id="compliance-agent",
                    evidence_refs=(evidence_label,),
                    confidence=min(1.0, top.score),
                    finding_id=f"agent-norm:{top.passage_id}",
                )
            )
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"hits={len(hits)}",
            ),
            issues,
            list(hits),
            None,
        )

    def _tool_compile_ids(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        assert self._ids_compiler is not None
        source = request.technical_spec_source or request.requirement_source
        try:
            draft = self._ids_compiler.compile(source)
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-IDS",
                        severity=Severity.INFO,
                        message=f"IDS draft compile failed: {exc}",
                        category=FindingCategory.IDS_VALIDATION,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        issues: list[ValidationIssue] = []
        if draft.source_requirement_count > 0 and draft.suggested_ids_xml:
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-AGENT-IDS-DRAFT",
                    severity=Severity.INFO,
                    message=(
                        f"[advisory] IDS draft compiled "
                        f"({draft.source_requirement_count} specs). "
                        f"{draft.rationale}"
                    ),
                    category=FindingCategory.IDS_VALIDATION,
                    source_id="compliance-agent",
                    confidence=draft.confidence,
                    finding_id="agent-ids-draft",
                )
            )
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"specs={draft.source_requirement_count}",
            ),
            issues,
            [],
            draft,
        )

    def _tool_verify_loads(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        assert self._load_verifier is not None
        try:
            raw = list(self._load_verifier.verify(request))
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-LOAD",
                        severity=Severity.INFO,
                        message=f"Agent load tool failed: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        # Re-tag as advisory agent findings (engine path already runs load verifier).
        advisory = [
            ValidationIssue(
                rule_id=f"AGENT-{issue.rule_id}",
                severity=Severity.INFO,
                message=f"[advisory-agent] {issue.message}",
                category=issue.category,
                target_ref=issue.target_ref,
                expected_value=issue.expected_value,
                observed_value=issue.observed_value,
                unit=issue.unit,
                source_id="compliance-agent",
                finding_id=f"agent-load:{issue.rule_id}:{issue.target_ref or ''}",
                confidence=0.5,
            )
            for issue in raw
            if issue.rule_id == "AEROBIM-LOAD-MISMATCH"
        ]
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"mismatches={len(advisory)}",
            ),
            advisory,
            [],
            None,
        )

    def _tool_analyze_logic(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        assert self._logic_analyzer is not None
        has_req = bool(
            request.requirement_source.text.strip() or request.requirement_source.path is not None
        )
        manifest = PackageManifest(
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            has_requirement_source=has_req,
            has_technical_spec=request.technical_spec_source is not None,
            has_calculation_source=request.calculation_source is not None,
            has_ids=request.ids_path is not None,
            drawing_count=len(request.drawing_sources),
            drawing_sheet_ids=tuple((source.sheet_id or "") for source in request.drawing_sources),
            pd_section_path=request.pd_section_path,
            rd_section_path=request.rd_section_path,
            revision=request.revision,
            stage=request.stage,
        )
        try:
            raw = list(self._logic_analyzer.analyze(manifest))
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-LOGIC",
                        severity=Severity.INFO,
                        message=f"Agent logic tool failed: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        advisory = [
            ValidationIssue(
                rule_id=f"AGENT-{issue.rule_id}",
                severity=Severity.INFO,
                message=f"[advisory-agent] {issue.message}",
                category=issue.category,
                source_id="compliance-agent",
                finding_id=f"agent-logic:{issue.rule_id}",
                confidence=0.6,
            )
            for issue in raw
        ]
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"findings={len(advisory)}",
            ),
            advisory,
            [],
            None,
        )

    def _tool_check_quantities(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        assert self._quantity_checker is not None
        # Agent has no requirement extractor; empty claims → skipped (not false "ok").
        claims = claims_from_area_requirements(())
        if not claims:
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="skipped",
                    detail="no area/volume claims in agent context (engine path owns qty)",
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-QTY-EMPTY",
                        severity=Severity.INFO,
                        message=(
                            "[advisory] Quantity tool skipped: no claims in agent context "
                            "(engine Analyze path uses extracted requirements)"
                        ),
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="compliance-agent",
                        finding_id="agent-qty:empty",
                        confidence=1.0,
                    )
                ],
                [],
                None,
            )
        try:
            raw = list(self._quantity_checker.check(request.ifc_path, claims))
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-QTY",
                        severity=Severity.INFO,
                        message=f"Agent quantity tool failed: {exc}",
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        advisory = [
            ValidationIssue(
                rule_id=f"AGENT-{issue.rule_id}",
                severity=Severity.INFO,
                message=f"[advisory-agent] {issue.message}",
                category=issue.category,
                target_ref=issue.target_ref,
                source_id="compliance-agent",
                finding_id=f"agent-qty:{issue.rule_id}:{issue.target_ref or ''}",
                confidence=0.5,
            )
            for issue in raw
        ]
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"findings={len(raw)}",
            ),
            advisory,
            [],
            None,
        )

    def _tool_detect_clashes(
        self,
        request: ValidationRequest,
        step: AgentToolStep,
    ) -> tuple[AgentToolStep, list[ValidationIssue], list[NormPassage], IdsCompileDraft | None]:
        assert self._clash_detector is not None
        try:
            results = list(self._clash_detector.detect(request.ifc_path))
        except Exception as exc:  # noqa: BLE001
            return (
                AgentToolStep(
                    tool_name=step.tool_name,
                    rationale=step.rationale,
                    arguments=step.arguments,
                    status="error",
                    detail=str(exc),
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-AGENT-CLASH",
                        severity=Severity.INFO,
                        message=f"Agent clash tool failed: {exc}",
                        category=FindingCategory.SPATIAL,
                        source_id="compliance-agent",
                    )
                ],
                [],
                None,
            )
        advisory = [
            ValidationIssue(
                rule_id="AEROBIM-AGENT-CLASH-HIT",
                severity=Severity.INFO,
                message=(
                    f"[advisory-agent] Clash probe: {clash.description} "
                    f"({clash.element_a_guid} × {clash.element_b_guid})"
                ),
                category=FindingCategory.SPATIAL,
                source_id="compliance-agent",
                finding_id=f"agent-clash:{clash.element_a_guid}:{clash.element_b_guid}",
                confidence=0.5,
            )
            for clash in results[:20]
        ]
        if not advisory:
            advisory.append(
                ValidationIssue(
                    rule_id="AEROBIM-AGENT-CLASH-NONE",
                    severity=Severity.INFO,
                    message="[advisory] Clash probe returned zero hits (generic ifcclash path)",
                    category=FindingCategory.SPATIAL,
                    source_id="compliance-agent",
                    finding_id="agent-clash:none",
                    confidence=1.0,
                )
            )
        return (
            AgentToolStep(
                tool_name=step.tool_name,
                rationale=step.rationale,
                arguments=step.arguments,
                status="ok",
                detail=f"clashes={len(results)}",
            ),
            advisory,
            [],
            None,
        )


def merge_advisory_sequences(
    *groups: Sequence[ValidationIssue],
) -> tuple[ValidationIssue, ...]:
    """Flatten advisory issue groups for DeterminismGate input."""

    merged: list[ValidationIssue] = []
    for group in groups:
        merged.extend(group)
    return tuple(merged)
