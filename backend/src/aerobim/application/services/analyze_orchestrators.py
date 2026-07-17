"""Contour orchestrators for AnalyzeProjectPackageUseCase (RT-A God-UseCase split).

UseCase retains public ``execute()`` contract and DI surface; each orchestrator owns
one contour. Host methods stay on the UseCase for behavior parity — orchestrators
coordinate phases and make contour boundaries testable in isolation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from aerobim.application.services.compliance_agent_orchestrator import merge_advisory_sequences
from aerobim.application.services.confidence_scorer import score_confidence
from aerobim.application.services.signoff_policy import summary_passed_after_capabilities
from aerobim.domain.drawing_region_hitl import (
    issues_for_hitl_regions,
    mark_regions_for_hitl,
    review_events_for_hitl_regions,
)
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.ingestion import detect_revision_merge_conflicts
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
    cad_capability: CapabilityStatus
    cad_issues: tuple[ValidationIssue, ...]
    region_hitl_issues: tuple[ValidationIssue, ...]
    norm_pack_capability: CapabilityStatus
    norm_pack_issues: tuple[ValidationIssue, ...]


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
    quantity_issues: tuple[ValidationIssue, ...]
    quantity_capability: CapabilityStatus | None
    load_issues: tuple[ValidationIssue, ...]
    calculation_match: CapabilityStatus
    logic_issues: tuple[ValidationIssue, ...]
    engine_issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class AdvisoryBundle:
    advisory_issues: tuple[ValidationIssue, ...]
    advisory_ids_draft: IdsCompileDraft | None
    reconciled_issues: tuple[ValidationIssue, ...]
    divergences: tuple[DivergenceRecord, ...]


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
        annotation_list, region_list = self._host._collect_drawing_annotations(request)
        cad_annotations, cad_capability, cad_issues = self._host._run_cad_ingest(request)
        drawing_annotations = tuple([*annotation_list, *cad_annotations])
        drawing_regions = mark_regions_for_hitl(tuple(region_list), drawing_annotations)
        region_hitl_issues = tuple(issues_for_hitl_regions(drawing_regions))
        drawing_assets = tuple(self._host._collect_drawing_assets(request))
        return IngestionBundle(
            request=request,
            requirements=requirements,
            drawing_annotations=drawing_annotations,
            drawing_regions=drawing_regions,
            drawing_assets=drawing_assets,
            cad_capability=cad_capability,
            cad_issues=tuple(cad_issues),
            region_hitl_issues=region_hitl_issues,
            norm_pack_capability=norm_pack_capability,
            norm_pack_issues=tuple(norm_pack_issues),
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
        cross_document_issues = tuple(
            self._host._detect_cross_document_contradictions(requirements)
        )
        revision_merge_issues = tuple(
            detect_revision_merge_conflicts(self._host._collect_identity_sources(request))
        )
        section_pairing_issues, section_pairing_capability = (
            self._host._collect_section_pairing_issues(request)
        )
        reinforcement_provenance_issues = tuple(
            self._host._apply_openrebar_provenance_policy(
                self._host._external_evidence_verifier.verify(request),
                request.reinforcement_provenance_mode,
            )
        )
        clash_results, clash_capability, clash_issues = self._host._run_clash_detection(
            request.ifc_path
        )
        mep_capability = self._host._probe_mep_system_graph(request.ifc_path)
        quantity_issues, quantity_capability = self._host._run_quantity_consistency(
            request.ifc_path, requirements
        )
        load_issues, calculation_match = self._host._run_load_evidence(request)
        logic_issues = self._host._run_logic_consistency(request)
        engine_issues = tuple(
            [
                *schema_issues_t,
                *ids_audit_issues,
                *ifc_issues,
                *drawing_issues,
                *cross_document_issues,
                *revision_merge_issues,
                *section_pairing_issues,
                *reinforcement_provenance_issues,
                *ids_issues,
                *clash_issues,
                *ingested.norm_pack_issues,
                *ingested.cad_issues,
                *quantity_issues,
                *load_issues,
                *logic_issues,
                *ingested.region_hitl_issues,
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
            quantity_issues=tuple(quantity_issues),
            quantity_capability=quantity_capability,
            load_issues=tuple(load_issues),
            calculation_match=calculation_match,
            logic_issues=tuple(logic_issues),
            engine_issues=engine_issues,
        )


class AdvisoryOrchestrator:
    """AI_ADVISORY — agent + DeterminismGate; never writes summary.passed alone."""

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def run(
        self,
        request: ValidationRequest,
        deterministic: DeterministicBundle,
    ) -> AdvisoryBundle:
        agent_advisory: tuple[ValidationIssue, ...] = ()
        advisory_ids_draft = None
        if self._host._compliance_agent is not None:
            agent_result = self._host._compliance_agent.run(request)
            agent_advisory = agent_result.advisory_issues
            advisory_ids_draft = agent_result.ids_draft
        reconciled_issues, divergences = self._host._determinism_gate.reconcile(
            engine_issues=list(deterministic.engine_issues),
            advisory_issues=merge_advisory_sequences(
                self._host._advisory_issues,
                agent_advisory,
            ),
        )
        return AdvisoryBundle(
            advisory_issues=agent_advisory,
            advisory_ids_draft=advisory_ids_draft,
            reconciled_issues=tuple(reconciled_issues),
            divergences=tuple(divergences),
        )


class EvidenceAssembler:
    """EVIDENCE_REPORTING — provenance, remarks, capabilities, persist."""

    def __init__(self, host: AnalyzeProjectPackageUseCase) -> None:
        self._host = host

    def assemble(
        self,
        request: ValidationRequest,
        ingested: IngestionBundle,
        deterministic: DeterministicBundle,
        advisory: AdvisoryBundle,
    ) -> ValidationReport:
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
            for issue in advisory.reconciled_issues
        )
        issues_with_remarks = tuple(self._host._attach_remarks(prioritized_issues))
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
            drawing_annotation_count=len(ingested.drawing_annotations),
            schema_issues=deterministic.schema_issues,
            ids_audit_issues=deterministic.ids_audit_issues,
            schema_request_id=deterministic.schema_request_id,
            norm_rule_packs=ingested.norm_pack_capability,
            section_pairing=deterministic.section_pairing_capability,
            dwg_dxf=ingested.cad_capability,
            mep_system_clash=deterministic.mep_capability,
            calculation_match=deterministic.calculation_match,
            quantity_capability=deterministic.quantity_capability,
        )
        enforce_honesty_capabilities(capabilities)
        passed = summary_passed_after_capabilities(
            error_count=error_count,
            capabilities=capabilities,
        )
        if self._host._clash_affects_pass:
            hard_clashes = tuple(
                clash
                for clash in deterministic.clash_results
                if getattr(clash, "clash_type", "hard") != "clearance"
            )
            if hard_clashes:
                passed = False

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
        )
        self._host._audit_report_store.save(report)
        if self._host._review_event_store is not None:
            for event in review_events_for_hitl_regions(
                report_id=report.report_id,
                regions=ingested.drawing_regions,
                created_at=report.created_at,
            ):
                self._host._review_event_store.append(event)
        persisted_report = self._host._audit_report_store.get(report.report_id)
        return persisted_report or report
