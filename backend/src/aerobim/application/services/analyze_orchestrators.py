"""Contour orchestrators for AnalyzeProjectPackageUseCase (RT-A God-UseCase split).

UseCase retains public ``execute()`` contract and DI surface; each orchestrator owns
one contour. Host methods stay on the UseCase for behavior parity — orchestrators
coordinate phases and make contour boundaries testable in isolation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.compliance_agent_orchestrator import merge_advisory_sequences
from aerobim.application.services.confidence_scorer import score_confidence
from aerobim.application.services.customer_intake import CustomerIntakeGate
from aerobim.application.services.determinism_gate import build_evidence_universe
from aerobim.application.services.package_outcome import compute_package_outcome
from aerobim.domain.annotation_ifc_matching import AnnotationIfcLink, match_annotations_to_regions
from aerobim.domain.drawing_region_hitl import (
    issues_for_hitl_regions,
    mark_regions_for_hitl,
    review_events_for_hitl_regions,
)
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.ingestion import (
    detect_annotation_sheet_identity_drift,
    detect_missing_drawing_sheet_identity,
    detect_revision_merge_conflicts,
)
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ClashResult,
    DivergenceRecord,
    DrawingAnnotation,
    DrawingAsset,
    DrawingRegionRef,
    FindingCategory,
    ParsedRequirement,
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
    compute_issue_priority,
)
from aerobim.domain.norm_assist import IdsCompileDraft
from aerobim.domain.package_outcome import summary_passed_from_outcome
from aerobim.domain.system_capabilities import enforce_honesty_capabilities

if TYPE_CHECKING:
    from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase


@dataclass(frozen=True)
class IngestionBundle:
    request: ValidationRequest
    requirements: tuple[ParsedRequirement, ...]
    drawing_annotations: tuple[DrawingAnnotation, ...]
    drawing_regions: tuple[DrawingRegionRef, ...]
    drawing_assets: tuple[DrawingAsset, ...]
    raster_annotation_count: int
    cad_capability: CapabilityStatus
    cad_issues: tuple[ValidationIssue, ...]
    region_hitl_issues: tuple[ValidationIssue, ...]
    norm_pack_capability: CapabilityStatus
    norm_pack_issues: tuple[ValidationIssue, ...]
    annotation_ifc_links: tuple[AnnotationIfcLink, ...] = ()
    extraction_integrity: CapabilityStatus | None = None


@dataclass(frozen=True)
class DeterministicBundle:
    schema_issues: tuple[ValidationIssue, ...]
    schema_request_id: str | None
    ids_audit_issues: tuple[ValidationIssue, ...]
    ids_issues: tuple[ValidationIssue, ...]
    ifc_issues: tuple[ValidationIssue, ...]
    drawing_issues: tuple[ValidationIssue, ...]
    cross_document_issues: tuple[ValidationIssue, ...]
    revision_merge_issues: tuple[ValidationIssue, ...]
    section_pairing_issues: tuple[ValidationIssue, ...]
    section_pairing_capability: CapabilityStatus
    reinforcement_provenance_issues: tuple[ValidationIssue, ...]
    clash_results: tuple[ClashResult, ...]
    clash_capability: CapabilityStatus
    clash_issues: tuple[ValidationIssue, ...]
    mep_capability: CapabilityStatus
    mep_issues: tuple[ValidationIssue, ...]
    quantity_issues: tuple[ValidationIssue, ...]
    quantity_capability: CapabilityStatus | None
    load_issues: tuple[ValidationIssue, ...]
    calculation_match: CapabilityStatus
    logic_issues: tuple[ValidationIssue, ...]
    engine_issues: tuple[ValidationIssue, ...]
    signature_capability: CapabilityStatus | None = None
    signature_issues: tuple[ValidationIssue, ...] = ()
    package_completeness_capability: CapabilityStatus | None = None
    package_completeness_issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True)
class AdvisoryBundle:
    advisory_issues: tuple[ValidationIssue, ...]
    advisory_ids_draft: IdsCompileDraft | None
    reconciled_issues: tuple[ValidationIssue, ...]
    divergences: tuple[DivergenceRecord, ...]
    tool_traces: tuple[dict[str, object], ...] = ()
    advisory_suppressed: bool = False
    """True when HybridRouteGate blocked advisory observation creation (WP-02)."""


class IngestionOrchestrator:
    """INGESTION contour — requirements, drawings, CAD, office hydrate."""

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def run(self, request: ValidationRequest) -> IngestionBundle:
        request = self._host._maybe_hydrate_office_requirement_source(request)
        structured_requirements = list(
            self._host._requirement_extractor.extract(request.requirement_source)
        )
        structured_requirements = [
            replace(req, confidence=score_confidence(req)) for req in structured_requirements
        ]
        synthesized_requirements = self._host._collect_synthesized_requirements(request)
        synthesized_requirements = [
            replace(req, confidence=score_confidence(req)) for req in synthesized_requirements
        ]
        norm_pack_requirements, norm_pack_capability = self._host._collect_norm_pack_requirements(
            request
        )
        norm_pack_issues: list[ValidationIssue] = []
        if norm_pack_capability.status is CapabilityState.FAILED:
            norm_pack_issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-NORM-PACK",
                    severity=Severity.ERROR,
                    message=norm_pack_capability.reason
                    or "Configured norm rule pack failed to load",
                    category=FindingCategory.IFC_VALIDATION,
                )
            )
        requirements = tuple(
            [*structured_requirements, *synthesized_requirements, *norm_pack_requirements]
        )
        annotation_list, region_list, raster_annotation_count = (
            self._host._collect_drawing_annotations(request)
        )
        cad_annotations, cad_capability, cad_issues = self._host._run_cad_ingest(request)
        drawing_annotations = tuple([*annotation_list, *cad_annotations])
        drawing_regions = mark_regions_for_hitl(tuple(region_list), drawing_annotations)
        region_hitl_issues = tuple(issues_for_hitl_regions(drawing_regions))
        annotation_ifc_links = tuple(
            match_annotations_to_regions(
                drawing_annotations,
                drawing_regions,
                requirements=requirements,
            )
        )
        drawing_assets = tuple(self._host._collect_drawing_assets(request))
        extraction_integrity = self._host._probe_extraction_integrity(request)
        return IngestionBundle(
            request=request,
            requirements=requirements,
            drawing_annotations=drawing_annotations,
            drawing_regions=drawing_regions,
            drawing_assets=drawing_assets,
            raster_annotation_count=raster_annotation_count,
            cad_capability=cad_capability,
            cad_issues=tuple(cad_issues),
            region_hitl_issues=region_hitl_issues,
            norm_pack_capability=norm_pack_capability,
            norm_pack_issues=tuple(norm_pack_issues),
            annotation_ifc_links=annotation_ifc_links,
            extraction_integrity=extraction_integrity,
        )


class DeterministicValidationOrchestrator:
    """DETERMINISTIC_VALIDATION — only contour that feeds summary.passed truth."""

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def run(
        self,
        request: ValidationRequest,
        ingested: IngestionBundle,
    ) -> DeterministicBundle:
        requirements = ingested.requirements
        if request.ifc_path is None:
            return self._run_document_only(request, ingested)

        schema_issues = list(self._host._collect_schema_issues(request.ifc_path))
        schema_request_id, schema_remote_issues = self._host._submit_bsi_validation(
            request.ifc_path
        )
        schema_issues.extend(schema_remote_issues)
        schema_issues_t = tuple(schema_issues)
        ids_audit_issues = tuple(self._host._collect_ids_audit_issues(request))
        ids_issues = tuple(self._host._collect_ids_issues(request))
        ifc_issues = (
            tuple(self._host._ifc_validator.validate(request.ifc_path, requirements))
            if requirements
            else ()
        )
        drawing_issues = tuple(
            self._host._validate_drawing_annotations(requirements, ingested.drawing_annotations)
        )
        sheet_identity_issues = tuple(
            [
                *detect_missing_drawing_sheet_identity(request.drawing_sources),
                *detect_annotation_sheet_identity_drift(
                    request.drawing_sources,
                    ingested.drawing_annotations,
                ),
            ]
        )
        cross_document_issues = tuple(
            self._host._detect_cross_document_contradictions(requirements)
        )
        revision_merge_issues = tuple(
            detect_revision_merge_conflicts(self._host._collect_identity_sources(request))
        )
        section_pairing_issues, section_pairing_capability = (
            self._host._collect_section_pairing_issues(request)
        )
        reinforcement_mode = request.reinforcement_provenance_mode
        # Hard profiles always enforce OpenRebar provenance (RTATOM-G07); soft stays advisory.
        if getattr(self._host, "_hard_signoff_profile", False):
            reinforcement_mode = "enforced"
        reinforcement_provenance_issues = tuple(
            self._host._apply_openrebar_provenance_policy(
                self._host._external_evidence_verifier.verify(request),
                reinforcement_mode,
            )
        )
        clash_results, clash_capability, clash_issues = self._host._run_clash_detection(
            request.ifc_path
        )
        mep_capability, mep_issues = self._host._probe_mep_system_graph(request.ifc_path)
        quantity_issues, quantity_capability = self._host._run_quantity_consistency(
            request.ifc_path, requirements
        )
        load_issues, calculation_match = self._host._run_load_evidence(request)
        logic_issues = self._host._run_logic_consistency(request)
        signature_capability, signature_issues = self._host._run_signature_audit(request)
        package_completeness_capability, package_completeness_issues = (
            self._host._run_package_completeness(request)
        )
        engine_issues = tuple(
            [
                *schema_issues_t,
                *ids_audit_issues,
                *ifc_issues,
                *drawing_issues,
                *sheet_identity_issues,
                *cross_document_issues,
                *revision_merge_issues,
                *section_pairing_issues,
                *reinforcement_provenance_issues,
                *ids_issues,
                *clash_issues,
                *mep_issues,
                *ingested.norm_pack_issues,
                *ingested.cad_issues,
                *quantity_issues,
                *load_issues,
                *logic_issues,
                *ingested.region_hitl_issues,
                *signature_issues,
                *package_completeness_issues,
            ]
        )
        return DeterministicBundle(
            schema_issues=schema_issues_t,
            schema_request_id=schema_request_id,
            ids_audit_issues=ids_audit_issues,
            ids_issues=ids_issues,
            ifc_issues=ifc_issues,
            drawing_issues=drawing_issues,
            cross_document_issues=cross_document_issues,
            revision_merge_issues=revision_merge_issues,
            section_pairing_issues=tuple(section_pairing_issues),
            section_pairing_capability=section_pairing_capability,
            reinforcement_provenance_issues=reinforcement_provenance_issues,
            clash_results=tuple(clash_results),
            clash_capability=clash_capability,
            clash_issues=tuple(clash_issues),
            mep_capability=mep_capability,
            mep_issues=tuple(mep_issues),
            quantity_issues=tuple(quantity_issues),
            quantity_capability=quantity_capability,
            load_issues=tuple(load_issues),
            calculation_match=calculation_match,
            logic_issues=tuple(logic_issues),
            engine_issues=engine_issues,
            signature_capability=signature_capability,
            signature_issues=tuple(signature_issues),
            package_completeness_capability=package_completeness_capability,
            package_completeness_issues=tuple(package_completeness_issues),
        )

    def _run_document_only(
        self,
        request: ValidationRequest,
        ingested: IngestionBundle,
    ) -> DeterministicBundle:
        """Partial package: no IFC — skip model-bound engines; keep document checks."""
        skip = CapabilityStatus(
            CapabilityState.SKIPPED,
            "ifc_path omitted — document/partial package mode; IFC engines not evaluated",
        )
        if getattr(self._host, "_require_clash", False):
            clash_capability = CapabilityStatus(
                CapabilityState.FAILED,
                "clash required but ifc_path omitted (document-only analyze)",
            )
            clash_issues: tuple[ValidationIssue, ...] = (
                ValidationIssue(
                    rule_id="AEROBIM-CLASH-CAPABILITY",
                    severity=Severity.ERROR,
                    message="Clash detection required but ifc_path was omitted",
                    category=FindingCategory.SPATIAL,
                    source_id="clash",
                ),
            )
        else:
            clash_capability = skip
            clash_issues = ()
        if getattr(self._host, "_require_mep_system_clash", False):
            mep_capability = CapabilityStatus(
                CapabilityState.FAILED,
                "MEP system clash required but ifc_path omitted",
            )
        else:
            # Honesty surface: mep_system_clash must not use SKIPPED.
            mep_capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "ifc_path omitted — MEP system graph not evaluated (document-only)",
            )
        requirements = ingested.requirements
        ids_audit_issues = tuple(self._host._collect_ids_audit_issues(request))
        # IDS against IFC cannot run without a model.
        ids_issues: tuple[ValidationIssue, ...]
        if request.ids_path is not None:
            ids_issues = (
                ValidationIssue(
                    rule_id="AEROBIM-IDS-CAPABILITY",
                    severity=Severity.ERROR,
                    message="IDS validation requested but ifc_path was omitted",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                ),
            )
        else:
            ids_issues = ()
        drawing_issues = tuple(
            self._host._validate_drawing_annotations(requirements, ingested.drawing_annotations)
        )
        sheet_identity_issues = tuple(
            [
                *detect_missing_drawing_sheet_identity(request.drawing_sources),
                *detect_annotation_sheet_identity_drift(
                    request.drawing_sources,
                    ingested.drawing_annotations,
                ),
            ]
        )
        cross_document_issues = tuple(
            self._host._detect_cross_document_contradictions(requirements)
        )
        revision_merge_issues = tuple(
            detect_revision_merge_conflicts(self._host._collect_identity_sources(request))
        )
        section_pairing_issues, section_pairing_capability = (
            self._host._collect_section_pairing_issues(request)
        )
        reinforcement_mode = request.reinforcement_provenance_mode
        if getattr(self._host, "_hard_signoff_profile", False):
            reinforcement_mode = "enforced"
        reinforcement_provenance_issues = tuple(
            self._host._apply_openrebar_provenance_policy(
                self._host._external_evidence_verifier.verify(request),
                reinforcement_mode,
            )
        )
        load_issues, calculation_match = self._host._run_load_evidence(request)
        logic_issues = self._host._run_logic_consistency(request)
        signature_capability, signature_issues = self._host._run_signature_audit(request)
        package_completeness_capability, package_completeness_issues = (
            self._host._run_package_completeness(request)
        )
        engine_issues = tuple(
            [
                *ids_audit_issues,
                *ids_issues,
                *drawing_issues,
                *sheet_identity_issues,
                *cross_document_issues,
                *revision_merge_issues,
                *section_pairing_issues,
                *reinforcement_provenance_issues,
                *clash_issues,
                *ingested.norm_pack_issues,
                *ingested.cad_issues,
                *load_issues,
                *logic_issues,
                *ingested.region_hitl_issues,
                *signature_issues,
                *package_completeness_issues,
            ]
        )
        return DeterministicBundle(
            schema_issues=(),
            schema_request_id=None,
            ids_audit_issues=ids_audit_issues,
            ids_issues=ids_issues,
            ifc_issues=(),
            drawing_issues=drawing_issues,
            cross_document_issues=cross_document_issues,
            revision_merge_issues=revision_merge_issues,
            section_pairing_issues=tuple(section_pairing_issues),
            section_pairing_capability=section_pairing_capability,
            reinforcement_provenance_issues=reinforcement_provenance_issues,
            clash_results=(),
            clash_capability=clash_capability,
            clash_issues=clash_issues,
            mep_capability=mep_capability,
            mep_issues=(),
            quantity_issues=(),
            quantity_capability=skip,
            load_issues=tuple(load_issues),
            calculation_match=calculation_match,
            logic_issues=tuple(logic_issues),
            engine_issues=engine_issues,
            signature_capability=signature_capability,
            signature_issues=tuple(signature_issues),
            package_completeness_capability=package_completeness_capability,
            package_completeness_issues=tuple(package_completeness_issues),
        )


class AdvisoryOrchestrator:
    """AI_ADVISORY — agent + DeterminismGate; never writes summary.passed alone.

    WP-02: ``HybridRouteGate`` is a mandatory pre-gate. When the route is not
    allowed, no advisory observation is created (empty findings / no agent run),
    and a gate audit row is recorded on ``tool_traces``.
    """

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def run(
        self,
        request: ValidationRequest,
        deterministic: DeterministicBundle,
        ingested: IngestionBundle | None = None,
    ) -> AdvisoryBundle:
        gate_trace, allowed = self._evaluate_hybrid_pre_gate(request)
        agent_advisory: tuple[ValidationIssue, ...] = ()
        advisory_ids_draft = None
        tool_traces: list[dict[str, object]] = []
        if gate_trace is not None:
            tool_traces.append(gate_trace)

        if allowed:
            if self._host._compliance_agent is not None:
                agent_result = self._host._compliance_agent.run(request)
                agent_advisory = agent_result.advisory_issues
                advisory_ids_draft = agent_result.ids_draft
                tool_traces.extend(agent_result.tool_traces or ())
            injected = self._host._advisory_issues
        else:
            # Fail closed: do not create advisory observations (including injected ones).
            injected = ()

        # TZ row 19: local IFC space inventory candidates (no egress). Always eligible —
        # HybridRouteGate only suppresses external/agent advisory, not local inventory.
        space_candidates: tuple = ()
        extractor = getattr(self._host, "_space_inventory_extractor", None)
        if (
            getattr(self._host, "_space_efficiency_advisory_enabled", False)
            and request.ifc_path is not None
            and extractor is not None
        ):
            from aerobim.domain.space_efficiency_advisory import (
                build_space_efficiency_candidates,
            )

            spaces = extractor.extract(request.ifc_path)
            space_candidates = build_space_efficiency_candidates(spaces)
            if space_candidates:
                tool_traces.append(
                    {
                        "tool": "space_efficiency_advisory",
                        "status": "ok",
                        "spaces": len(spaces),
                        "candidates": len(space_candidates),
                        "verdict_impact": "none",
                        "claim": "ADVISORY_ONLY; no efficiency threshold; expert confirmation",
                    }
                )

        # Wave J: ground advisory references against the deterministic universe.
        evidence_universe = build_evidence_universe(
            engine_issues=deterministic.engine_issues,
            requirements=ingested.requirements if ingested is not None else (),
            clash_results=deterministic.clash_results,
            drawing_annotations=(ingested.drawing_annotations if ingested is not None else ()),
        )
        reconciled_issues, divergences = self._host._determinism_gate.reconcile(
            engine_issues=list(deterministic.engine_issues),
            advisory_issues=merge_advisory_sequences(
                injected,
                agent_advisory,
                space_candidates,
            ),
            evidence_universe=evidence_universe,
        )
        return AdvisoryBundle(
            advisory_issues=agent_advisory if allowed else (),
            advisory_ids_draft=advisory_ids_draft if allowed else None,
            reconciled_issues=tuple(reconciled_issues),
            divergences=tuple(divergences),
            tool_traces=tuple(tool_traces),
            advisory_suppressed=not allowed,
        )

    def _evaluate_hybrid_pre_gate(
        self, request: ValidationRequest
    ) -> tuple[dict[str, object] | None, bool]:
        """Return (audit_trace, may_create_advisory). Missing gate → suppress."""

        from aerobim.domain.hybrid.trust_policy import RouteTarget

        gate = getattr(self._host, "_hybrid_route_gate", None)
        if gate is None:
            return (
                {
                    "tool": "hybrid_route_gate",
                    "status": "blocked",
                    "reason": "hybrid_route_gate not configured; advisory suppressed",
                    "egress_bytes_estimate": 0,
                    "verdict_impact": "none",
                },
                False,
            )
        tenant_id = (request.tenant_id or "").strip()
        result = gate.evaluate(
            object_kind=_advisory_object_kind(request),
            target=RouteTarget.LOCAL,
            tenant_id=tenant_id,
            task_type="advisory_compliance_agent",
            request_id=request.request_id,
            project_id=request.project_id,
            payload=None,
        )
        trace = {
            "tool": "hybrid_route_gate",
            "status": result.decision.status.value,
            "allowed": result.may_create_advisory,
            "may_call_external": result.may_call_external,
            "reason": result.decision.reason,
            "classification": result.decision.classification.value,
            "target": result.decision.target.value,
            "egress_bytes_estimate": result.egress_bytes_estimate,
            "verdict_impact": result.audit_event.verdict_impact,
            "event_id": result.audit_event.event_id,
        }
        return trace, result.may_create_advisory


_PUBLIC_CORPUS_CHILDREN = frozenset(
    {
        "ifc",
        "drawings",
        "packages",
        "ids",
        "benchmarks",
        "bcf-xsd",
        "ids-xsd",
        "requirements",
        "mep",
        "cad",
        "config",
    }
)


def _advisory_object_kind(request: ValidationRequest) -> str:
    """Conservative object kind for advisory routing (never PUBLIC by default).

    Trusted public fixtures are only repo corpus trees under discrete ``samples`` /
    ``fixtures`` path components followed by a known public child (``ifc``, …).

    Never classify from absolute-path substrings alone (deploy under
    ``…/samples/AeroBIM/var/tenants/…`` must stay confidential). Never treat
    ``samples/customer`` or tenant uploads as public.
    """

    raw = getattr(request, "ifc_path", None)
    if raw is None:
        return "ifc"
    parts = [part.lower() for part in Path(str(raw)).parts]
    if "tenants" in parts or "uploads" in parts or "customer" in parts:
        return "ifc"
    for index, part in enumerate(parts):
        if part not in {"samples", "fixtures"}:
            continue
        if index + 1 >= len(parts):
            continue
        if parts[index + 1] in _PUBLIC_CORPUS_CHILDREN:
            return "public_fixture"
    return "ifc"


def _llm_overlay_route_target(provider: object):
    """Studio/cloud OpenAI-compat → PUBLIC; local weights / mock → LOCAL (RT-030)."""

    from aerobim.domain.hybrid.trust_policy import RouteTarget

    name = (
        str(getattr(provider, "provider", None) or getattr(provider, "_provider", "") or "")
        .strip()
        .lower()
    )
    if "yandex" in name or name in {"openai", "openai-compat", "openai_compat"}:
        return RouteTarget.PUBLIC
    return RouteTarget.LOCAL


class EvidenceAssembler:
    """EVIDENCE_REPORTING — provenance, remarks, capabilities, persist."""

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def _evaluate_llm_overlay_gate(
        self, request: ValidationRequest
    ) -> tuple[bool, dict[str, object] | None]:
        """HybridRouteGate before Studio/local remark overlay (RT-030 / WP-02 parity).

        Missing gate → suppress. Cloud (Yandex) uses PUBLIC target — CONFIDENTIAL IFC
        packages stay blocked (Claims Lock). Local/mock uses LOCAL.
        """

        from aerobim.domain.hybrid.trust_policy import RouteStatus
        from aerobim.domain.llm_advisory import DisabledLlmProvider

        provider = getattr(self._host, "_llm_advisory_provider", None)
        if provider is None or isinstance(provider, DisabledLlmProvider):
            return True, None

        gate = getattr(self._host, "_hybrid_route_gate", None)
        if gate is None:
            return (
                False,
                {
                    "tool": "hybrid_route_gate",
                    "status": "blocked",
                    "task_type": "advisory_remark_overlay",
                    "reason": "hybrid_route_gate not configured; llm overlay suppressed",
                    "egress_bytes_estimate": 0,
                    "verdict_impact": "none",
                },
            )

        target = _llm_overlay_route_target(provider)
        tenant_id = (request.tenant_id or "").strip()
        result = gate.evaluate(
            object_kind=_advisory_object_kind(request),
            target=target,
            tenant_id=tenant_id,
            task_type="advisory_remark_overlay",
            request_id=request.request_id,
            project_id=request.project_id,
            payload=None,
        )
        allowed = result.may_create_advisory
        if result.decision.status is RouteStatus.HUMAN_REVIEW:
            allowed = False
        trace = {
            "tool": "hybrid_route_gate",
            "status": result.decision.status.value,
            "allowed": allowed,
            "may_call_external": result.may_call_external,
            "reason": result.decision.reason,
            "classification": result.decision.classification.value,
            "target": result.decision.target.value,
            "task_type": "advisory_remark_overlay",
            "egress_bytes_estimate": result.egress_bytes_estimate,
            "verdict_impact": result.audit_event.verdict_impact,
            "event_id": result.audit_event.event_id,
        }
        return allowed, trace

    def assemble(
        self,
        request: ValidationRequest,
        ingested: IngestionBundle,
        deterministic: DeterministicBundle,
        advisory: AdvisoryBundle,
    ) -> ValidationReport:
        intake_issues: list[ValidationIssue] = []
        intake_blocked = False
        # Phase B: only samolet_pilot requires full customer intake (not fixture/dev CI).
        if self._host._signoff_profile == "samolet_pilot":
            gate_path = self._host._customer_intake_gate_path or CustomerIntakeGate.default_path()
            intake = CustomerIntakeGate.evaluate(gate_path)
            if not intake.ok:
                intake_blocked = True
                reason_text = "; ".join(intake.reasons) if intake.reasons else intake.status
                intake_issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-CUSTOMER-INTAKE",
                        severity=Severity.ERROR,
                        message=(f"Customer pilot intake blocked Shared-gate: {reason_text}"),
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="customer-intake-gate",
                        evidence_refs=(f"intake:{gate_path.as_posix()}",),
                        origin="deterministic",
                    )
                )

        prioritized_issues = tuple(
            ensure_finding_provenance(
                replace(
                    issue,
                    priority=compute_issue_priority(issue, profile=self._host._priority_profile),
                ),
                tenant_id=request.tenant_id,
                project_id=request.project_id or request.project_name,
                revision=request.revision,
            )
            for issue in [*intake_issues, *advisory.reconciled_issues]
        )
        issues_with_remarks = tuple(self._host._attach_remarks(prioritized_issues))
        overlay_traces: list[dict[str, object]] = []
        may_overlay, overlay_trace = self._evaluate_llm_overlay_gate(request)
        if overlay_trace is not None:
            overlay_traces.append(overlay_trace)
        if may_overlay:
            # Only trusted corpus prefixes may authorize synthetic_public egress.
            allow_synth = _advisory_object_kind(request) == "public_fixture"
            issues_with_remarks, llm_advisory_capability = self._host._overlay_llm_remarks(
                issues_with_remarks,
                request_id=request.request_id,
                allow_synthetic_public=allow_synth,
            )
        else:
            reason = (overlay_trace or {}).get("reason") or "hybrid_route_gate blocked"
            llm_advisory_capability = CapabilityStatus(
                CapabilityState.SKIPPED,
                f"llm advisory skipped ({reason}); advisory drafts only; never sets "
                "summary.passed; ai_generated requires expert confirmation",
            )
        severity_counts = Counter(issue.severity for issue in issues_with_remarks)
        error_count = severity_counts[Severity.ERROR]
        warning_count = severity_counts[Severity.WARNING]

        capabilities = self._host._build_capabilities(
            requirements=ingested.requirements,
            ifc_issues=deterministic.ifc_issues,
            ids_path=request.ids_path,
            ids_issues=deterministic.ids_issues,
            clash_capability=deterministic.clash_capability,
            drawing_sources=request.drawing_sources,
            drawing_annotation_count=ingested.raster_annotation_count,
            schema_issues=deterministic.schema_issues,
            ids_audit_issues=deterministic.ids_audit_issues,
            schema_request_id=deterministic.schema_request_id,
            norm_rule_packs=ingested.norm_pack_capability,
            section_pairing=deterministic.section_pairing_capability,
            dwg_dxf=ingested.cad_capability,
            mep_system_clash=deterministic.mep_capability,
            calculation_match=deterministic.calculation_match,
            quantity_capability=deterministic.quantity_capability,
            extraction_integrity=ingested.extraction_integrity,
            qualified_signature=deterministic.signature_capability,
            package_completeness=deterministic.package_completeness_capability,
        )
        if request.ifc_path is None:
            skip_ifc = CapabilityStatus(
                CapabilityState.SKIPPED,
                "ifc_path omitted — document/partial package mode",
            )
            capabilities = replace(
                capabilities,
                ifc_validation=skip_ifc,
                ifc_schema=skip_ifc,
                unit_scale=CapabilityStatus(
                    CapabilityState.NOT_VERIFIED,
                    "ifc_path omitted — IFC unit scale not probed",
                ),
            )
        capabilities = replace(capabilities, llm_advisory=llm_advisory_capability)
        enforce_honesty_capabilities(capabilities)
        policy = build_signoff_policy(
            profile=self._host._signoff_profile,
            require_clash=self._host._require_clash,
            clash_affects_pass=self._host._clash_affects_pass,
            require_bsi_schema=self._host._require_bsi_schema,
            require_mep_system_clash=self._host._require_mep_system_clash,
        )
        hard_clash_blocks = False
        if policy.clash_affects_pass:
            hard_clashes = tuple(
                clash
                for clash in deterministic.clash_results
                if getattr(clash, "clash_type", "hard") != "clearance"
            )
            if hard_clashes:
                hard_clash_blocks = True

        hitl_requires_review = any(
            bool(getattr(region, "hitl_required", False)) for region in ingested.drawing_regions
        )
        outcome = compute_package_outcome(
            error_count=error_count,
            warning_count=warning_count,
            capabilities=capabilities,
            intake_blocked=intake_blocked,
            hitl_requires_review=hitl_requires_review,
            hard_clash_blocks=hard_clash_blocks,
            policy=policy,
        )
        passed = summary_passed_from_outcome(outcome)

        # Soft Shared-gate honesty: soft-profile passed must not claim production verdict.
        soft_profile = policy.profile in {"development", "fixture"}
        authoritative = not (soft_profile and passed)

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=ingested.requirements,
            issues=issues_with_remarks,
            summary=ValidationSummary(
                requirement_count=len(ingested.requirements),
                issue_count=len(issues_with_remarks),
                error_count=error_count,
                warning_count=warning_count,
                passed=passed,
                drawing_annotation_count=len(ingested.drawing_annotations),
                generated_remark_count=sum(
                    1 for issue in issues_with_remarks if issue.remark is not None
                ),
                authoritative=authoritative,
                outcome=outcome,
            ),
            drawing_annotations=ingested.drawing_annotations,
            drawing_assets=ingested.drawing_assets,
            clash_results=deterministic.clash_results,
            capabilities=capabilities,
            schema_validation_request_id=deterministic.schema_request_id,
            project_name=request.project_name,
            discipline=request.discipline,
            stage=request.stage,
            information_container_id=request.information_container_id,
            revision=request.revision,
            doc_status=request.doc_status,
            tenant_id=request.tenant_id,
            project_id=request.project_id,
            divergences=advisory.divergences,
            advisory_ids_draft=advisory.advisory_ids_draft,
            drawing_regions=ingested.drawing_regions,
            annotation_ifc_links=tuple(
                link.as_dict()
                for link in self._host._confirm_annotation_ifc_links(
                    ingested.annotation_ifc_links,
                    request.ifc_path,
                )
            ),
            tool_traces=tuple([*advisory.tool_traces, *overlay_traces]),
        )
        # HITL trail before report persist: never save a report without audit events
        # when regions require HITL. Orphan events on save failure are reconcilesable;
        # report-without-trail is a false-pass integrity hole (RT-ADV-HITL-TX).
        if self._host._review_event_store is not None:
            for event in review_events_for_hitl_regions(
                report_id=report.report_id,
                regions=ingested.drawing_regions,
                created_at=report.created_at,
            ):
                self._host._review_event_store.append(event)
        try:
            self._host._audit_report_store.save(report)
        except Exception:
            if self._host._review_event_store is not None:
                discard = getattr(self._host._review_event_store, "discard_report", None)
                if callable(discard):
                    discard(report.report_id)
            raise
        persisted_report = self._host._audit_report_store.get(report.report_id)
        return persisted_report or report
