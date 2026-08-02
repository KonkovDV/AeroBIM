from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path

from aerobim.application.services.analyze_orchestrators import (
    AdvisoryOrchestrator,
    DeterministicValidationOrchestrator,
    EvidenceAssembler,
    IngestionOrchestrator,
)
from aerobim.application.services.capability_matrix import (
    RASTER_DRAWING_FORMATS,
    RASTER_DRAWING_SUFFIXES,
    build_report_capabilities,
)
from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.application.services.compliance_agent_orchestrator import (
    ComplianceAgentOrchestrator,
)
from aerobim.application.services.cross_document_contradictions import (
    CrossDocumentContradictionDetector,
    to_float,
)
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.services.drawing_annotation_validation import (
    DrawingAnnotationValidator,
)
from aerobim.application.services.extraction_integrity_probe import probe_extraction_integrity
from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.application.services.mep_scope_probe import MepScopeProbe
from aerobim.application.services.package_ingestion import PackageIngestionService
from aerobim.application.services.spatial_predicates import issues_from_clash_results
from aerobim.domain.annotation_ifc_matching import AnnotationIfcLink
from aerobim.domain.architecture import Contour
from aerobim.domain.consistency import PackageManifest, claims_from_area_requirements
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.mep import (
    FederatedMepScope,
    MepSystemGraph,
    MepSystemGraphProvider,
)
from aerobim.domain.mep_aabb import MepAabbPairFilter
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ComparisonOperator,
    ConflictKind,
    DrawingAnnotation,
    DrawingAsset,
    DrawingRegionRef,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    ReportCapabilities,
    RequirementSource,
    Severity,
    ToleranceConfig,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.domain.package_trace import PackageTraceCollector
from aerobim.domain.ports import (
    AuditReportStore,
    BsiValidationService,
    CadModelIngestor,
    ClashDetector,
    DocumentSignatureAuditor,
    DrawingAnalyzer,
    ExternalEvidenceVerifier,
    ExtractionIntegritySignalProducer,
    IdsDocumentAuditor,
    IdsValidator,
    IfcSchemaValidator,
    IfcSpatialIndexProvider,
    IfcValidator,
    LoadEvidenceVerifier,
    LogicConsistencyAnalyzer,
    MultimodalDrawingPipeline,
    NarrativeRuleSynthesizer,
    NormRulePackLoader,
    OfficeDocumentIngestor,
    QuantityConsistencyChecker,
    RasterDrawingAnalyzer,
    RemarkGenerator,
    RequirementExtractor,
    ReviewEventStore,
    SectionDiffAnalyzer,
)
from aerobim.domain.quantity import QuantityValue

_RASTER_DRAWING_SUFFIXES = RASTER_DRAWING_SUFFIXES
_RASTER_DRAWING_FORMATS = RASTER_DRAWING_FORMATS
_DRAWING_ASSET_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
_CAD_DRAWING_SUFFIXES = {".dxf", ".dwg"}
_OFFICE_SUFFIXES = {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".odt", ".ods"}
_OPENREBAR_REPORT_CONTRACT_ID = "OpenRebar.reinforcement.report.v1"
_OPENREBAR_WARNING_SEVERITY_CLASS: dict[str, str] = {
    "OPENREBAR-CONTRACT": "critical",
    "OPENREBAR-PROVENANCE-DIGEST": "critical",
    "OPENREBAR-PROVENANCE-REFERENCE-MISSING": "critical",
    "OPENREBAR-OPT-FALLBACK": "major",
    "OPENREBAR-OPT-STRATEGY": "major",
    "OPENREBAR-WASTE-METRIC-MISSING": "major",
    "OPENREBAR-WASTE-THRESHOLD": "major",
    "OPENREBAR-PROJECT-CODE": "minor",
}
_OPENREBAR_ENFORCED_ESCALATION_CLASSES = {"critical", "major"}


_logger = logging.getLogger("aerobim.analyze")


class _NullExternalEvidenceVerifier:
    def verify(self, request: ValidationRequest) -> list[ValidationIssue]:
        return []


class AnalyzeProjectPackageUseCase:
    def __init__(
        self,
        requirement_extractor: RequirementExtractor,
        narrative_rule_synthesizer: NarrativeRuleSynthesizer,
        drawing_analyzer: DrawingAnalyzer,
        ifc_validator: IfcValidator,
        remark_generator: RemarkGenerator,
        audit_report_store: AuditReportStore,
        ids_validator: IdsValidator | None = None,
        raster_drawing_analyzer: RasterDrawingAnalyzer | None = None,
        tolerance: ToleranceConfig | None = None,
        clash_detector: ClashDetector | None = None,
        cross_doc_severity: str = "warning",
        priority_profile: str = "default",
        external_evidence_verifier: ExternalEvidenceVerifier | None = None,
        clash_affects_pass: bool = False,
        require_clash: bool = False,
        require_bsi_schema: bool = False,
        require_mep_system_clash: bool = False,
        signoff_profile: str = "development",
        ifc_schema_validator: IfcSchemaValidator | None = None,
        ids_document_auditor: IdsDocumentAuditor | None = None,
        bsi_validation_service: BsiValidationService | None = None,
        norm_rule_pack_loader: NormRulePackLoader | None = None,
        section_diff_analyzer: SectionDiffAnalyzer | None = None,
        default_norm_rule_pack_path: Path | None = None,
        cad_model_ingestor: CadModelIngestor | None = None,
        office_document_ingestor: OfficeDocumentIngestor | None = None,
        mep_system_graph_provider: MepSystemGraphProvider | None = None,
        determinism_gate: DeterminismGate | None = None,
        advisory_issues: Sequence[ValidationIssue] | None = None,
        quantity_consistency_checker: QuantityConsistencyChecker | None = None,
        load_evidence_verifier: LoadEvidenceVerifier | None = None,
        logic_consistency_analyzer: LogicConsistencyAnalyzer | None = None,
        multimodal_drawing_pipeline: MultimodalDrawingPipeline | None = None,
        compliance_agent: ComplianceAgentOrchestrator | None = None,
        review_event_store: ReviewEventStore | None = None,
        customer_intake_gate_path: Path | None = None,
        mep_federated_scope_path: Path | None = None,
        mep_aabb_pair_filter: MepAabbPairFilter | None = None,
        mep_aabb_filter_enabled: bool = True,
        extraction_integrity_producer: ExtractionIntegritySignalProducer | None = None,
        hybrid_route_gate: HybridRouteGate | None = None,
        document_signature_auditor: DocumentSignatureAuditor | None = None,
    ) -> None:
        self._requirement_extractor = requirement_extractor
        self._narrative_rule_synthesizer = narrative_rule_synthesizer
        self._drawing_analyzer = drawing_analyzer
        self._ifc_validator = ifc_validator
        self._ids_validator = ids_validator
        self._raster_drawing_analyzer = raster_drawing_analyzer
        self._remark_generator = remark_generator
        self._audit_report_store = audit_report_store
        self._tolerance = tolerance or ToleranceConfig()
        self._clash_detector = clash_detector
        self._clash_affects_pass = clash_affects_pass
        self._require_clash = require_clash
        self._require_bsi_schema = require_bsi_schema
        self._require_mep_system_clash = require_mep_system_clash
        self._signoff_profile = signoff_profile
        _valid_severities = {"error", "warning", "info"}
        # Hard profiles always escalate cross-doc contradictions to ERROR (RTATOM-G05).
        hard_profile = signoff_profile in {"samolet_pilot", "production"}
        effective_cross_doc = "error" if hard_profile else cross_doc_severity
        self._cross_doc_severity = Severity(
            effective_cross_doc if effective_cross_doc in _valid_severities else "warning"
        )
        self._hard_signoff_profile = hard_profile
        self._priority_profile = (
            priority_profile if priority_profile in {"default", "samolet"} else "default"
        )
        self._external_evidence_verifier = (
            external_evidence_verifier or _NullExternalEvidenceVerifier()
        )
        self._ifc_schema_validator = ifc_schema_validator
        self._ids_document_auditor = ids_document_auditor
        self._bsi_validation_service = bsi_validation_service
        self._norm_rule_pack_loader = norm_rule_pack_loader
        self._section_diff_analyzer = section_diff_analyzer
        self._default_norm_rule_pack_path = default_norm_rule_pack_path
        self._cad_model_ingestor = cad_model_ingestor
        self._office_document_ingestor = office_document_ingestor
        self._mep_system_graph_provider = mep_system_graph_provider
        self._determinism_gate = determinism_gate or DeterminismGate()
        self._advisory_issues = tuple(advisory_issues or ())
        self._quantity_consistency_checker = quantity_consistency_checker
        self._load_evidence_verifier = load_evidence_verifier
        self._logic_consistency_analyzer = logic_consistency_analyzer
        self._multimodal_drawing_pipeline = multimodal_drawing_pipeline
        self._compliance_agent = compliance_agent
        self._review_event_store = review_event_store
        self._customer_intake_gate_path = customer_intake_gate_path
        self._mep_federated_scope_path = mep_federated_scope_path
        self._mep_aabb_pair_filter = mep_aabb_pair_filter
        self._mep_aabb_filter_enabled = mep_aabb_filter_enabled
        self._extraction_integrity_producer = extraction_integrity_producer
        self._hybrid_route_gate = hybrid_route_gate
        self._document_signature_auditor = document_signature_auditor
        self._package_trace_collector = None
        self._ingestion = IngestionOrchestrator(self)
        self._deterministic = DeterministicValidationOrchestrator(self)
        self._advisory = AdvisoryOrchestrator(self)
        self._evidence = EvidenceAssembler(self)

    def execute(self, request: ValidationRequest) -> ValidationReport:
        collector: PackageTraceCollector | None = self._package_trace_collector
        if collector is None:
            ingested = self._ingestion.run(request)
            request = ingested.request
            if not ingested.requirements and request.ids_path is None:
                raise ValueError(
                    "No requirements were extracted or synthesized from the provided sources"
                )
            deterministic = self._deterministic.run(request, ingested)
            advisory = self._advisory.run(request, deterministic, ingested)
            return self._evidence.assemble(request, ingested, deterministic, advisory)

        with collector.span(Contour.INGESTION):
            ingested = self._ingestion.run(request)
        request = ingested.request
        if not ingested.requirements and request.ids_path is None:
            raise ValueError(
                "No requirements were extracted or synthesized from the provided sources"
            )
        with collector.span(Contour.DETERMINISTIC_VALIDATION):
            deterministic = self._deterministic.run(request, ingested)
        with collector.span(Contour.AI_ADVISORY):
            advisory = self._advisory.run(request, deterministic, ingested)
        with collector.span(Contour.EVIDENCE_REPORTING):
            return self._evidence.assemble(request, ingested, deterministic, advisory)

    def _cross_doc_detector(self) -> CrossDocumentContradictionDetector:
        # Built on demand: tests construct partial instances and mutate _tolerance.
        return CrossDocumentContradictionDetector(
            self._tolerance,
            getattr(self, "_cross_doc_severity", Severity.WARNING),
        )

    def _annotation_validator(self) -> DrawingAnnotationValidator:
        return DrawingAnnotationValidator(self._tolerance)

    def _mep_probe(self) -> MepScopeProbe:
        return MepScopeProbe(
            self._mep_system_graph_provider,
            self._mep_federated_scope_path,
            self._repo_root,
            aabb_filter=self._mep_aabb_pair_filter,
            aabb_filter_enabled=self._mep_aabb_filter_enabled,
        )

    def _ingestion_service(self) -> PackageIngestionService:
        # Built on demand: tests monkeypatch injected ports after construction.
        return PackageIngestionService(
            drawing_analyzer=self._drawing_analyzer,
            narrative_rule_synthesizer=self._narrative_rule_synthesizer,
            raster_drawing_analyzer=self._raster_drawing_analyzer,
            multimodal_drawing_pipeline=self._multimodal_drawing_pipeline,
            cad_model_ingestor=self._cad_model_ingestor,
            office_document_ingestor=self._office_document_ingestor,
            norm_rule_pack_loader=self._norm_rule_pack_loader,
            default_norm_rule_pack_path=self._default_norm_rule_pack_path,
        )

    def _maybe_hydrate_office_requirement_source(
        self, request: ValidationRequest
    ) -> ValidationRequest:
        return self._ingestion_service().maybe_hydrate_office_requirement_source(request)

    def _run_cad_ingest(
        self, request: ValidationRequest
    ) -> tuple[tuple[DrawingAnnotation, ...], CapabilityStatus, list[ValidationIssue]]:
        return self._ingestion_service().run_cad_ingest(request)

    def _load_mep_federated_scope(self) -> FederatedMepScope | None:
        return self._mep_probe().load_scope()

    def _probe_mep_system_graph(
        self, ifc_path: Path
    ) -> tuple[CapabilityStatus, tuple[ValidationIssue, ...]]:
        return self._mep_probe().probe(ifc_path)

    def _repo_root(self) -> Path:
        # use_cases → application → aerobim → src → backend → repo
        return Path(__file__).resolve().parents[5]

    def _evaluate_mep_clearance_matrix(
        self,
        graph: MepSystemGraph,
        scope: FederatedMepScope | None,
    ) -> tuple[ValidationIssue, ...]:
        # Note: MepScopeProbe.probe() evaluates the matrix internally; this
        # delegate exists for direct callers only and is not on the probe path.
        return self._mep_probe().evaluate_clearance_matrix(graph, scope)

    def _run_quantity_consistency(
        self,
        ifc_path: Path,
        requirements: Sequence[ParsedRequirement],
    ) -> tuple[list[ValidationIssue], CapabilityStatus | None]:
        """Return issues and optional capability override (FAILED on infra errors)."""

        claims = claims_from_area_requirements(requirements)
        if not claims:
            return [], None
        if self._quantity_consistency_checker is None:
            # Claims present but checker absent: not a silent skip (false-pass).
            return (
                [],
                CapabilityStatus(
                    CapabilityState.NOT_VERIFIED,
                    "QuantityConsistencyChecker not configured while area claims present",
                ),
            )
        try:
            return list(
                self._quantity_consistency_checker.check(ifc_path, claims)
            ), CapabilityStatus(CapabilityState.OK, "quantity consistency evaluated")
        except Exception as exc:
            _logger.exception("Quantity consistency check failed for %s", ifc_path)
            # RT-C: infrastructure exception → ERROR + FAILED capability (blocks pass)
            return (
                [
                    ValidationIssue(
                        rule_id="AEROBIM-QTY-ERROR",
                        severity=Severity.ERROR,
                        message=f"Quantity consistency infrastructure failure: {exc}",
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="quantity-consistency",
                    )
                ],
                CapabilityStatus(
                    CapabilityState.FAILED,
                    f"Quantity consistency infrastructure failure: {exc}",
                ),
            )

    def _run_load_evidence(
        self, request: ValidationRequest
    ) -> tuple[list[ValidationIssue], CapabilityStatus]:
        if request.calculation_source is None:
            return (
                [],
                CapabilityStatus(
                    CapabilityState.SKIPPED, "numeric calculation match not evaluated"
                ),
            )
        if self._load_evidence_verifier is None:
            return (
                [],
                CapabilityStatus(CapabilityState.SKIPPED, "LoadEvidenceVerifier not configured"),
            )
        try:
            issues = list(self._load_evidence_verifier.verify(request))
        except Exception as exc:
            _logger.exception("Load evidence verify failed for request %s", request.request_id)
            return (
                [
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-ERROR",
                        severity=Severity.ERROR,
                        message=f"Load evidence infrastructure failure: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="load-evidence",
                    )
                ],
                CapabilityStatus(
                    CapabilityState.FAILED,
                    f"Load evidence infrastructure failure: {exc}",
                ),
            )
        mismatches = [i for i in issues if i.rule_id == "AEROBIM-LOAD-MISMATCH"]
        unevaluated = any(
            i.rule_id
            in {
                "AEROBIM-LOAD-FORMAT",
                "AEROBIM-LOAD-SCHEMA",
                "AEROBIM-LOAD-JSON",
                "AEROBIM-LOAD-ROW",
            }
            for i in issues
        )
        evaluated_ok = any(i.rule_id == "AEROBIM-LOAD-OK" for i in issues)
        if mismatches:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                f"{len(mismatches)} load match failure(s)",
            )
        elif unevaluated or not evaluated_ok:
            capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "Load evidence present but сверка not fully evaluated",
            )
        else:
            capability = CapabilityStatus(
                CapabilityState.OK,
                "Load evidence numeric match evaluated",
            )
        return issues, capability

    def _run_logic_consistency(self, request: ValidationRequest) -> list[ValidationIssue]:
        if self._logic_consistency_analyzer is None:
            return []
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
        return list(self._logic_consistency_analyzer.analyze(manifest))

    def _effective_clash_affects_pass(self) -> bool:
        """Hard profiles always force clash_affects_pass via sign-off policy (RT D03/G01)."""

        return build_signoff_policy(
            profile=self._signoff_profile,
            require_clash=self._require_clash,
            clash_affects_pass=self._clash_affects_pass,
            require_bsi_schema=self._require_bsi_schema,
            require_mep_system_clash=self._require_mep_system_clash,
        ).clash_affects_pass

    def _run_clash_detection(
        self, ifc_path
    ) -> tuple[tuple, CapabilityStatus, list[ValidationIssue]]:
        if self._clash_detector is None:
            if self._require_clash:
                issue = ValidationIssue(
                    rule_id="AEROBIM-CLASH-CAPABILITY",
                    severity=Severity.ERROR,
                    message="Clash detection required but detector is not configured",
                    category=FindingCategory.SPATIAL,
                    source_id="clash",
                )
                return (
                    (),
                    CapabilityStatus(CapabilityState.FAILED, "clash detector not configured"),
                    [issue],
                )
            return (
                (),
                CapabilityStatus(CapabilityState.SKIPPED, "clash detector not configured"),
                [],
            )
        try:
            results = tuple(self._clash_detector.detect(ifc_path))
            return (
                results,
                CapabilityStatus(CapabilityState.OK),
                issues_from_clash_results(
                    results,
                    affects_pass=self._effective_clash_affects_pass(),
                ),
            )
        except ClashCapabilityError as exc:
            skipped = exc.status == "skipped"
            # Required clash must never green-pass on a missing optional stack.
            if skipped and self._require_clash:
                state = CapabilityState.FAILED
            else:
                state = CapabilityState.SKIPPED if skipped else CapabilityState.FAILED
            severity = Severity.ERROR if state == CapabilityState.FAILED else Severity.WARNING
            issue = ValidationIssue(
                rule_id="AEROBIM-CLASH-CAPABILITY",
                severity=severity,
                message=f"Clash detection capability {exc.status}: {exc.reason}",
                category=FindingCategory.SPATIAL,
                source_id="clash",
            )
            return (), CapabilityStatus(state, exc.reason), [issue]
        except Exception as exc:  # noqa: BLE001
            issue = ValidationIssue(
                rule_id="AEROBIM-CLASH-CAPABILITY",
                severity=Severity.ERROR,
                message=f"Clash detection capability failed: {exc}",
                category=FindingCategory.SPATIAL,
                source_id="clash",
            )
            return (
                (),
                CapabilityStatus(CapabilityState.FAILED, str(exc)),
                [issue],
            )

    def _build_capabilities(
        self,
        *,
        requirements,
        ifc_issues,
        ids_path,
        ids_issues,
        clash_capability: CapabilityStatus,
        drawing_sources,
        drawing_annotation_count: int = 0,
        schema_issues=(),
        ids_audit_issues=(),
        schema_request_id: str | None = None,
        norm_rule_packs: CapabilityStatus | None = None,
        section_pairing: CapabilityStatus | None = None,
        dwg_dxf: CapabilityStatus | None = None,
        mep_system_clash: CapabilityStatus | None = None,
        calculation_match: CapabilityStatus | None = None,
        quantity_capability: CapabilityStatus | None = None,
        extraction_integrity: CapabilityStatus | None = None,
        qualified_signature: CapabilityStatus | None = None,
    ) -> ReportCapabilities:
        return build_report_capabilities(
            requirements=requirements,
            ifc_issues=ifc_issues,
            ids_path=ids_path,
            ids_issues=ids_issues,
            clash_capability=clash_capability,
            drawing_sources=drawing_sources,
            drawing_annotation_count=drawing_annotation_count,
            schema_issues=schema_issues,
            ids_audit_issues=ids_audit_issues,
            schema_request_id=schema_request_id,
            norm_rule_packs=norm_rule_packs,
            section_pairing=section_pairing,
            dwg_dxf=dwg_dxf,
            mep_system_clash=mep_system_clash,
            calculation_match=calculation_match,
            quantity_capability=quantity_capability,
            extraction_integrity=extraction_integrity,
            qualified_signature=qualified_signature,
            ids_validator_configured=self._ids_validator is not None,
            ifc_schema_validator_configured=self._ifc_schema_validator is not None,
            require_bsi_schema=self._require_bsi_schema,
            raster_analyzer_configured=self._raster_drawing_analyzer is not None,
        )

    def _run_signature_audit(
        self, request: ValidationRequest
    ) -> tuple[CapabilityStatus | None, list[ValidationIssue]]:
        """Optional detached-envelope audit on ifc_path (deterministic contour).

        Runs when ``signature_envelope_path`` is set or ``require_signature_audit``.
        Never claims УКЭП legal validity; trust chain stays not_verified.
        """

        should_run = request.require_signature_audit or request.signature_envelope_path is not None
        if not should_run:
            return None, []

        from aerobim.domain.signature_immutability import (
            CLAIM_BOUNDARY,
            missing_envelope_result,
        )

        auditor = self._document_signature_auditor
        if auditor is None:
            if request.require_signature_audit:
                reason = (
                    "signature audit required but DocumentSignatureAuditor not configured; "
                    f"{CLAIM_BOUNDARY}"
                )
                return (
                    CapabilityStatus(CapabilityState.FAILED, reason),
                    [
                        ValidationIssue(
                            rule_id="AEROBIM-SIGNATURE-MISSING",
                            severity=Severity.ERROR,
                            message=reason,
                            category=FindingCategory.IFC_VALIDATION,
                            source_id="signature-audit",
                            origin="deterministic",
                            evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                        )
                    ],
                )
            return None, []

        result = auditor.audit(
            request.ifc_path,
            envelope_path=request.signature_envelope_path,
            required_roles=request.required_signer_roles,
        )
        capability = result.to_capability_status()
        issues: list[ValidationIssue] = []
        if request.require_signature_audit and "missing_envelope" in result.reasons:
            # Explicit missing required envelope: FAILED + blocking ERROR.
            failed = missing_envelope_result(reason="missing_envelope")
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                "; ".join([*failed.reasons, failed.claim_boundary]),
            )
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-SIGNATURE-MISSING",
                    severity=Severity.ERROR,
                    message=(
                        "Required detached signature envelope missing next to content "
                        f"(or at signature_envelope_path); {CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="signature-audit",
                    origin="deterministic",
                    evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                )
            )
        elif result.overall_status == "failed":
            issues.append(
                ValidationIssue(
                    rule_id="AEROBIM-SIGNATURE-AUDIT",
                    severity=Severity.ERROR,
                    message=(
                        "Detached signature envelope audit failed "
                        f"({', '.join(result.reasons)}); {CLAIM_BOUNDARY}"
                    ),
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="signature-audit",
                    origin="deterministic",
                    evidence_refs=("claim_boundary:signature_ENG_PARTIAL",),
                )
            )
        return capability, issues

    def _probe_extraction_integrity(self, request: ValidationRequest) -> CapabilityStatus:
        return probe_extraction_integrity(
            self._extraction_integrity_producer,
            request.drawing_sources,
        )

    def _submit_bsi_validation(self, ifc_path) -> tuple[str | None, list[ValidationIssue]]:
        if self._bsi_validation_service is None:
            return None, []
        try:
            request_id = self._bsi_validation_service.submit(ifc_path)
            return request_id, []
        except Exception as exc:  # noqa: BLE001 — surface remote/local cert failures
            severity = Severity.ERROR if self._require_bsi_schema else Severity.WARNING
            return None, [
                ValidationIssue(
                    rule_id="AEROBIM-BSI-VALIDATION",
                    severity=severity,
                    message=f"bSI Validation Service / schema certificate submit failed: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="bsi-schema",
                )
            ]

    def _collect_schema_issues(self, ifc_path) -> list[ValidationIssue]:
        if self._ifc_schema_validator is None:
            return []
        return list(self._ifc_schema_validator.validate_schema(ifc_path))

    def _collect_ids_audit_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_document_auditor is None:
            # RT D04: never silent-skip a requested IDS document audit.
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-AUDIT-CAPABILITY",
                    severity=Severity.ERROR,
                    message=(
                        "IDS document audit requested but no ids document auditor is configured"
                    ),
                    category=FindingCategory.IDS_VALIDATION,
                    source_id="ids",
                )
            ]
        return list(self._ids_document_auditor.audit(request.ids_path))

    def _collect_ids_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_validator is None:
            # Requested IDS must fail closed — never crash the package contour.
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-CAPABILITY",
                    severity=Severity.ERROR,
                    message="IDS validation requested but no ids validator is configured",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                )
            ]
        try:
            return list(self._ids_validator.validate(request.ids_path, request.ifc_path))
        except Exception as exc:  # noqa: BLE001 — adapter I/O must not silent-pass
            _logger.exception("IDS validation failed for %s", request.ids_path)
            return [
                ValidationIssue(
                    rule_id="AEROBIM-IDS-ERROR",
                    severity=Severity.ERROR,
                    message=f"IDS validation infrastructure failure: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="ids",
                )
            ]

    def _apply_openrebar_provenance_policy(
        self,
        issues: Sequence[ValidationIssue],
        mode: str,
    ) -> list[ValidationIssue]:
        if mode != "enforced":
            return list(issues)

        escalated: list[ValidationIssue] = []
        for issue in issues:
            if issue.severity != Severity.WARNING:
                escalated.append(issue)
                continue

            severity_class = _OPENREBAR_WARNING_SEVERITY_CLASS.get(issue.rule_id, "major")
            if severity_class not in _OPENREBAR_ENFORCED_ESCALATION_CLASSES:
                escalated.append(issue)
                continue

            escalated.append(
                ValidationIssue(
                    rule_id=issue.rule_id,
                    severity=Severity.ERROR,
                    message=issue.message,
                    ifc_entity=issue.ifc_entity,
                    category=issue.category,
                    target_ref=issue.target_ref,
                    property_set=issue.property_set,
                    property_name=issue.property_name,
                    operator=issue.operator,
                    expected_value=issue.expected_value,
                    observed_value=issue.observed_value,
                    unit=issue.unit,
                    element_guid=issue.element_guid,
                    problem_zone=issue.problem_zone,
                    remark=issue.remark,
                )
            )

        return escalated

    def _collect_norm_pack_requirements(
        self,
        request: ValidationRequest,
    ) -> tuple[list[ParsedRequirement], CapabilityStatus]:
        return self._ingestion_service().collect_norm_pack_requirements(request)

    def _load_norm_packs(
        self,
        pack_paths: Sequence[Path],
        *,
        source: str,
        tolerant: bool,
    ) -> tuple[list[ParsedRequirement], CapabilityStatus]:
        return self._ingestion_service().load_norm_packs(
            pack_paths, source=source, tolerant=tolerant
        )

    def _collect_section_pairing_issues(
        self,
        request: ValidationRequest,
    ) -> tuple[tuple[ValidationIssue, ...], CapabilityStatus]:
        pd_path = request.pd_section_path
        rd_path = request.rd_section_path
        if pd_path is None and rd_path is None:
            return (), CapabilityStatus(
                CapabilityState.SKIPPED, "PD/RD section pairing not requested"
            )
        if pd_path is None or rd_path is None:
            raise ValueError(
                "PD/RD section pairing requires both pd_section_path and rd_section_path"
            )
        if self._section_diff_analyzer is None:
            raise RuntimeError("PD/RD section pairing requested but no analyzer is configured")
        report = self._section_diff_analyzer.analyze(pd_path, rd_path)
        reason = report.capability_reason(pd_path.name, rd_path.name)
        # Honest capability: unrecognized discipline, zero canonical coverage, or
        # residual unrecognized keys (raw-normalize pairing without registry) cannot
        # look like a successful pairing.
        if (
            (not report.discipline.recognized)
            or (report.pd_key_count > 0 and report.recognized_key_count == 0)
            or bool(report.unrecognized_keys)
        ):
            return report.issues, CapabilityStatus(CapabilityState.FAILED, reason)
        return report.issues, CapabilityStatus(CapabilityState.OK, reason)

    def _collect_synthesized_requirements(
        self, request: ValidationRequest
    ) -> list[ParsedRequirement]:
        return self._ingestion_service().collect_synthesized_requirements(request)

    def _collect_drawing_annotations(
        self, request: ValidationRequest
    ) -> tuple[list[DrawingAnnotation], list[DrawingRegionRef], int]:
        return self._ingestion_service().collect_drawing_annotations(request)

    def _collect_drawing_assets(self, request: ValidationRequest) -> list[DrawingAsset]:
        return self._ingestion_service().collect_drawing_assets(request)

    def _collect_raster_annotations(
        self,
        drawing_source: DrawingSource,
    ) -> list[DrawingAnnotation]:
        return self._ingestion_service().collect_raster_annotations(drawing_source)

    def _has_structured_drawing_input(self, drawing_source: DrawingSource) -> bool:
        return self._ingestion_service().has_structured_drawing_input(drawing_source)

    def _collect_identity_sources(self, request: ValidationRequest) -> list[RequirementSource]:
        return self._ingestion_service().collect_identity_sources(request)

    def _is_raster_drawing_source(self, drawing_source: DrawingSource) -> bool:
        return self._ingestion_service().is_raster_drawing_source(drawing_source)

    def _detect_cross_document_contradictions(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        return self._cross_doc_detector().detect(requirements)

    def _detect_ambiguous_property_set_alignments(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        return self._cross_doc_detector().detect_ambiguous_property_set_alignments(requirements)

    def _resolve_quantity(
        self,
        value: str | None,
        unit: str | None,
        quantity: QuantityValue | None,
    ) -> QuantityValue | None:
        return self._cross_doc_detector().resolve_quantity(value, unit, quantity)

    def _classify_conflict_kind(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> ConflictKind:
        return self._cross_doc_detector().classify_conflict_kind(
            value_a,
            unit_a,
            value_b,
            unit_b,
            quantity_a=quantity_a,
            quantity_b=quantity_b,
        )

    def _values_soft_conflict(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> bool:
        """True when same-unit numeric strings differ but stay within ε."""
        return self._cross_doc_detector().values_soft_conflict(
            value_a,
            unit_a,
            value_b,
            unit_b,
            quantity_a=quantity_a,
            quantity_b=quantity_b,
        )

    def _values_conflict(
        self,
        value_a: str | None,
        unit_a: str | None,
        value_b: str | None,
        unit_b: str | None,
        *,
        quantity_a: QuantityValue | None = None,
        quantity_b: QuantityValue | None = None,
    ) -> bool:
        """Return True when two expected values are materially different.

        Numeric pairs are compared with ε-tolerance from ``ToleranceConfig``;
        non-numeric pairs use case-insensitive string comparison.
        """
        return self._cross_doc_detector().values_conflict(
            value_a,
            unit_a,
            value_b,
            unit_b,
            quantity_a=quantity_a,
            quantity_b=quantity_b,
        )

    def _normalize_cross_document_numeric_value(
        self,
        value: float,
        unit: str | None,
    ) -> tuple[float, str] | None:
        return self._cross_doc_detector().normalize_numeric_value(value, unit)

    def _validate_drawing_annotations(
        self,
        requirements: Sequence[ParsedRequirement],
        drawing_annotations: Sequence[DrawingAnnotation],
    ) -> list[ValidationIssue]:
        return self._annotation_validator().validate(requirements, drawing_annotations)

    def _attach_remarks(self, issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
        enriched: list[ValidationIssue] = []
        for issue in issues:
            enriched.append(replace(issue, remark=self._remark_generator.generate(issue)))
        return enriched

    def _confirm_annotation_ifc_links(
        self,
        links: Sequence[AnnotationIfcLink],
        ifc_path: Path,
    ) -> tuple[AnnotationIfcLink, ...]:
        """Presence-check claimed annotation GUIDs against IFC spatial index."""

        from aerobim.domain.annotation_ifc_matching import confirm_annotation_ifc_links

        if not links:
            return ()
        validator = self._ifc_validator
        if isinstance(validator, IfcSpatialIndexProvider):
            index = validator.spatial_index_for(ifc_path)
        else:
            index = None
        return tuple(confirm_annotation_ifc_links(links, index))

    def _matches_annotation(
        self, requirement: ParsedRequirement, annotation: DrawingAnnotation
    ) -> bool:
        return self._annotation_validator().matches_annotation(requirement, annotation)

    def _compare_values(
        self,
        observed_value: str | None,
        expected_value: str | None,
        operator: ComparisonOperator,
        unit: str | None = None,
    ) -> bool:
        """Compare observed vs expected using fuzzy ε-tolerance for numerics."""
        return self._annotation_validator().compare_values(
            observed_value,
            expected_value,
            operator,
            unit=unit,
        )

    def _to_float(self, raw: str) -> float | None:
        return to_float(raw)
