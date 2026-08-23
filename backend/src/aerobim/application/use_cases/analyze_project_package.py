from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from aerobim.application.services.analyze_orchestrators import (
    AdvisoryOrchestrator,
    DeterministicValidationOrchestrator,
    EvidenceAssembler,
    IngestionOrchestrator,
)
from aerobim.application.services.capability_matrix import build_report_capabilities
from aerobim.application.services.capability_policy import apply_demo_scope_honesty
from aerobim.application.services.clash_detection_runner import ClashDetectionRunner
from aerobim.application.services.compliance_agent_orchestrator import (
    ComplianceAgentOrchestrator,
)
from aerobim.application.services.cross_document_contradictions import (
    CrossDocumentContradictionDetector,
)
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.services.drawing_annotation_validation import (
    DrawingAnnotationValidator,
)
from aerobim.application.services.extraction_integrity_probe import probe_extraction_integrity
from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.application.services.ids_compliance_runner import IdsComplianceRunner
from aerobim.application.services.mep_scope_probe import MepScopeProbe
from aerobim.application.services.package_ingestion import PackageIngestionService
from aerobim.application.services.remark_enricher import RemarkEnricher
from aerobim.application.services.signature_audit_runner import SignatureAuditRunner
from aerobim.domain.annotation_ifc_matching import AnnotationIfcLink
from aerobim.domain.architecture import Contour
from aerobim.domain.llm_advisory import LlmProvider
from aerobim.domain.mep import MepSystemGraphProvider
from aerobim.domain.mep_aabb import MepAabbPairFilter
from aerobim.domain.models import (
    CapabilityStatus,
    DrawingSource,
    ParsedRequirement,
    ReportCapabilities,
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
    IfcSpaceInventoryExtractor,
    IfcSpatialIndexProvider,
    IfcValidator,
    LoadEvidenceVerifier,
    LogicConsistencyAnalyzer,
    MultimodalDrawingPipeline,
    NarrativeRuleSynthesizer,
    NormRulePackLoader,
    OfficeDocumentIngestor,
    PackageInventoryLoader,
    QuantityConsistencyChecker,
    RasterDrawingAnalyzer,
    RemarkGenerator,
    RequirementExtractor,
    ReviewEventStore,
    SectionDiffAnalyzer,
)


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
        package_inventory_loader: PackageInventoryLoader | None = None,
        llm_advisory_provider: LlmProvider | None = None,
        remark_locale: str = "ru",
        llm_advisory_max_issues: int = 32,
        llm_max_concurrent: int = 4,
        space_efficiency_advisory_enabled: bool = True,
        space_inventory_extractor: IfcSpaceInventoryExtractor | None = None,
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
        demo_profile = signoff_profile in {"samolet_pilot_demo", "moscow_agr_2026"}
        effective_cross_doc = "error" if hard_profile or demo_profile else cross_doc_severity
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
        self._package_inventory_loader = package_inventory_loader
        self._llm_advisory_provider = llm_advisory_provider
        self._remark_locale = (
            "en" if (remark_locale or "ru").strip().lower().startswith("en") else "ru"
        )
        self._llm_advisory_max_issues = max(0, int(llm_advisory_max_issues))
        self._llm_max_concurrent = max(1, min(int(llm_max_concurrent), 10))
        self._space_efficiency_advisory_enabled = bool(space_efficiency_advisory_enabled)
        self._space_inventory_extractor = space_inventory_extractor
        self._package_trace_collector = None
        self._ingestion = IngestionOrchestrator(self)
        self._deterministic = DeterministicValidationOrchestrator(self)
        self._advisory = AdvisoryOrchestrator(self)
        self._evidence = EvidenceAssembler(self)

    def _clash_runner(self) -> ClashDetectionRunner:
        return ClashDetectionRunner(
            clash_detector=self._clash_detector,
            require_clash=self._require_clash,
            clash_affects_pass=self._clash_affects_pass,
            signoff_profile=self._signoff_profile,
            require_bsi_schema=self._require_bsi_schema,
            require_mep_system_clash=self._require_mep_system_clash,
            quantity_consistency_checker=self._quantity_consistency_checker,
            load_evidence_verifier=self._load_evidence_verifier,
            logic_consistency_analyzer=self._logic_consistency_analyzer,
        )

    def _ids_runner(self) -> IdsComplianceRunner:
        return IdsComplianceRunner(
            ids_validator=self._ids_validator,
            ids_document_auditor=self._ids_document_auditor,
            ifc_schema_validator=self._ifc_schema_validator,
            bsi_validation_service=self._bsi_validation_service,
            section_diff_analyzer=self._section_diff_analyzer,
            require_bsi_schema=self._require_bsi_schema,
        )

    def _signature_runner(self) -> SignatureAuditRunner:
        return SignatureAuditRunner(
            document_signature_auditor=self._document_signature_auditor,
            package_inventory_loader=self._package_inventory_loader,
        )

    def _remark_enricher(self) -> RemarkEnricher:
        return RemarkEnricher(
            remark_generator=self._remark_generator,
            llm_advisory_provider=self._llm_advisory_provider,
            remark_locale=self._remark_locale,
            llm_advisory_max_issues=self._llm_advisory_max_issues,
            llm_max_concurrent=self._llm_max_concurrent,
        )

    def execute(self, request: ValidationRequest) -> ValidationReport:
        collector: PackageTraceCollector | None = self._package_trace_collector
        if collector is None and self._hard_signoff_profile:
            collector = PackageTraceCollector(enforce_timeouts=True)
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

    def _repo_root(self) -> Path:
        # use_cases → application → aerobim → src → backend → repo
        return Path(__file__).resolve().parents[5]

    def _build_capabilities(
        self,
        *,
        requirements: Sequence[ParsedRequirement],
        ifc_issues: Sequence[ValidationIssue],
        ids_path: Path | None,
        ids_issues: Sequence[ValidationIssue],
        clash_capability: CapabilityStatus,
        drawing_sources: Sequence[DrawingSource],
        drawing_annotation_count: int = 0,
        schema_issues: Sequence[ValidationIssue] = (),
        ids_audit_issues: Sequence[ValidationIssue] = (),
        schema_request_id: str | None = None,
        norm_rule_packs: CapabilityStatus | None = None,
        section_pairing: CapabilityStatus | None = None,
        dwg_dxf: CapabilityStatus | None = None,
        mep_system_clash: CapabilityStatus | None = None,
        calculation_match: CapabilityStatus | None = None,
        quantity_capability: CapabilityStatus | None = None,
        extraction_integrity: CapabilityStatus | None = None,
        qualified_signature: CapabilityStatus | None = None,
        package_completeness: CapabilityStatus | None = None,
        office_ingest: CapabilityStatus | None = None,
    ) -> ReportCapabilities:
        assembled = build_report_capabilities(
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
            package_completeness=package_completeness,
            office_ingest=office_ingest,
            ids_validator_configured=self._ids_validator is not None,
            ifc_schema_validator_configured=self._ifc_schema_validator is not None,
            require_bsi_schema=self._require_bsi_schema,
            raster_analyzer_configured=self._raster_drawing_analyzer is not None,
        )
        if self._signoff_profile in {"samolet_pilot_demo", "moscow_agr_2026"}:
            return apply_demo_scope_honesty(assembled, profile=self._signoff_profile)
        return assembled

    def _probe_extraction_integrity(self, request: ValidationRequest) -> CapabilityStatus:
        return probe_extraction_integrity(
            self._extraction_integrity_producer,
            request.drawing_sources,
        )

    def _confirm_annotation_ifc_links(
        self,
        links: Sequence[AnnotationIfcLink],
        ifc_path: Path | None,
    ) -> tuple[AnnotationIfcLink, ...]:
        """Presence-check claimed annotation GUIDs against IFC spatial index."""

        from aerobim.domain.annotation_ifc_matching import confirm_annotation_ifc_links

        if not links or ifc_path is None:
            return ()
        validator = self._ifc_validator
        if isinstance(validator, IfcSpatialIndexProvider):
            index = validator.spatial_index_for(ifc_path)
        else:
            index = None
        return tuple(confirm_annotation_ifc_links(links, index))
