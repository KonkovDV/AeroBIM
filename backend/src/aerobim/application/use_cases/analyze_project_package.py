from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.application.services.confidence_scorer import score_confidence
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.services.signoff_policy import summary_passed_after_capabilities
from aerobim.application.services.spatial_predicates import issues_from_clash_results
from aerobim.domain.consistency import PackageManifest, claims_from_area_requirements
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.finding_provenance import ensure_finding_provenance
from aerobim.domain.ingestion import (
    detect_revision_merge_conflicts,
    stamp_requirement_source,
)
from aerobim.domain.mep import MepSystemGraphProvider
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ComparisonOperator,
    ConflictKind,
    DrawingAnnotation,
    DrawingAsset,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    ReportCapabilities,
    RequirementSource,
    RulePackStatus,
    RuleScope,
    Severity,
    SourceKind,
    ToleranceConfig,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
    ValidationSummary,
    compute_issue_priority,
    issue_from_requirement,
)
from aerobim.domain.ports import (
    AuditReportStore,
    BsiValidationService,
    CadModelIngestor,
    ClashDetector,
    DrawingAnalyzer,
    ExternalEvidenceVerifier,
    IdsDocumentAuditor,
    IdsValidator,
    IfcSchemaValidator,
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
    SectionDiffAnalyzer,
)
from aerobim.domain.quantity import QuantityValue, parse_quantity, si_compare

_RASTER_DRAWING_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
_RASTER_DRAWING_FORMATS = {"pdf", "png", "jpg", "jpeg", "webp", "image", "raster"}
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
_CROSS_DOC_UNIT_TO_SI_FACTOR: dict[str, tuple[str, float]] = {
    "m": ("m", 1.0),
    "м": ("m", 1.0),
    "mm": ("m", 0.001),
    "мм": ("m", 0.001),
    "cm": ("m", 0.01),
    "см": ("m", 0.01),
    "ft": ("m", 0.3048),
    "feet": ("m", 0.3048),
    "foot": ("m", 0.3048),
    "in": ("m", 0.0254),
    "inch": ("m", 0.0254),
    "inches": ("m", 0.0254),
    "m2": ("m2", 1.0),
    "м2": ("m2", 1.0),
    "m²": ("m2", 1.0),
    "м²": ("m2", 1.0),
    "sqm": ("m2", 1.0),
    "sq.m": ("m2", 1.0),
    "m3": ("m3", 1.0),
    "м3": ("m3", 1.0),
    "m³": ("m3", 1.0),
    "м³": ("m3", 1.0),
}


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
        _valid_severities = {"error", "warning", "info"}
        self._cross_doc_severity = Severity(
            cross_doc_severity if cross_doc_severity in _valid_severities else "warning"
        )
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

    def execute(self, request: ValidationRequest) -> ValidationReport:
        request = self._maybe_hydrate_office_requirement_source(request)
        structured_requirements = list(
            self._requirement_extractor.extract(request.requirement_source)
        )
        structured_requirements = [
            ParsedRequirement(
                **{k: v for k, v in req.__dict__.items() if k != "confidence"},
                confidence=score_confidence(req),
            )
            for req in structured_requirements
        ]
        synthesized_requirements = self._collect_synthesized_requirements(request)
        synthesized_requirements = [
            ParsedRequirement(
                **{k: v for k, v in req.__dict__.items() if k != "confidence"},
                confidence=score_confidence(req),
            )
            for req in synthesized_requirements
        ]
        norm_pack_requirements, norm_pack_capability = self._collect_norm_pack_requirements(request)
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
        schema_issues = list(self._collect_schema_issues(request.ifc_path))
        schema_request_id, schema_remote_issues = self._submit_bsi_validation(request.ifc_path)
        schema_issues.extend(schema_remote_issues)
        schema_issues_t = tuple(schema_issues)
        ids_audit_issues = tuple(self._collect_ids_audit_issues(request))
        ids_issues = tuple(self._collect_ids_issues(request))
        if not requirements and request.ids_path is None:
            raise ValueError(
                "No requirements were extracted or synthesized from the provided sources"
            )

        drawing_annotations = tuple(self._collect_drawing_annotations(request))
        cad_annotations, cad_capability, cad_issues = self._run_cad_ingest(request)
        drawing_annotations = tuple([*drawing_annotations, *cad_annotations])
        ifc_issues = (
            tuple(self._ifc_validator.validate(request.ifc_path, requirements))
            if requirements
            else ()
        )
        drawing_issues = tuple(
            self._validate_drawing_annotations(requirements, drawing_annotations)
        )
        drawing_assets = tuple(self._collect_drawing_assets(request))
        cross_document_issues = tuple(self._detect_cross_document_contradictions(requirements))
        revision_merge_issues = tuple(
            detect_revision_merge_conflicts(self._collect_identity_sources(request))
        )
        section_pairing_issues, section_pairing_capability = self._collect_section_pairing_issues(
            request
        )
        reinforcement_provenance_issues = tuple(
            self._apply_openrebar_provenance_policy(
                self._external_evidence_verifier.verify(request),
                request.reinforcement_provenance_mode,
            )
        )
        clash_results, clash_capability, clash_issues = self._run_clash_detection(request.ifc_path)
        mep_capability = self._probe_mep_system_graph(request.ifc_path)
        quantity_issues = self._run_quantity_consistency(request.ifc_path, requirements)
        load_issues, calculation_match = self._run_load_evidence(request)
        logic_issues = self._run_logic_consistency(request)
        raw_issues = [
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
            *norm_pack_issues,
            *cad_issues,
            *quantity_issues,
            *load_issues,
            *logic_issues,
        ]
        reconciled_issues, _divergences = self._determinism_gate.reconcile(
            engine_issues=raw_issues,
            advisory_issues=self._advisory_issues,
        )
        prioritized_issues = tuple(
            ensure_finding_provenance(
                ValidationIssue(
                    **{k: v for k, v in issue.__dict__.items() if k != "priority"},
                    priority=compute_issue_priority(issue, profile=self._priority_profile),
                ),
                tenant_id=request.tenant_id,
                project_id=request.project_id or request.project_name,
                revision=request.revision,
            )
            for issue in reconciled_issues
        )
        issues_with_remarks = tuple(self._attach_remarks(prioritized_issues))

        severity_counts = Counter(issue.severity for issue in issues_with_remarks)
        error_count = severity_counts[Severity.ERROR]
        warning_count = severity_counts[Severity.WARNING]

        capabilities = self._build_capabilities(
            requirements=requirements,
            ifc_issues=ifc_issues,
            ids_path=request.ids_path,
            ids_issues=ids_issues,
            clash_capability=clash_capability,
            drawing_sources=request.drawing_sources,
            drawing_annotation_count=len(drawing_annotations),
            schema_issues=schema_issues_t,
            ids_audit_issues=ids_audit_issues,
            schema_request_id=schema_request_id,
            norm_rule_packs=norm_pack_capability,
            section_pairing=section_pairing_capability,
            dwg_dxf=cad_capability,
            mep_system_clash=mep_capability,
            calculation_match=calculation_match,
        )
        passed = summary_passed_after_capabilities(
            error_count=error_count,
            capabilities=capabilities,
        )
        if self._clash_affects_pass:
            hard_clashes = tuple(
                clash
                for clash in clash_results
                if getattr(clash, "clash_type", "hard") != "clearance"
            )
            if hard_clashes:
                passed = False

        report = ValidationReport(
            report_id=uuid4().hex,
            request_id=request.request_id,
            ifc_path=request.ifc_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=requirements,
            issues=issues_with_remarks,
            summary=ValidationSummary(
                requirement_count=len(requirements),
                issue_count=len(issues_with_remarks),
                error_count=error_count,
                warning_count=warning_count,
                passed=passed,
                drawing_annotation_count=len(drawing_annotations),
                generated_remark_count=sum(
                    1 for issue in issues_with_remarks if issue.remark is not None
                ),
            ),
            drawing_annotations=drawing_annotations,
            drawing_assets=drawing_assets,
            clash_results=clash_results,
            capabilities=capabilities,
            schema_validation_request_id=schema_request_id,
            project_name=request.project_name,
            discipline=request.discipline,
            stage=request.stage,
            information_container_id=request.information_container_id,
            revision=request.revision,
            doc_status=request.doc_status,
            tenant_id=request.tenant_id,
            project_id=request.project_id,
        )
        self._audit_report_store.save(report)
        persisted_report = self._audit_report_store.get(report.report_id)
        return persisted_report or report

    def _maybe_hydrate_office_requirement_source(
        self, request: ValidationRequest
    ) -> ValidationRequest:
        source = request.requirement_source
        if source.text.strip() or source.path is None or self._office_document_ingestor is None:
            return request
        if source.path.suffix.lower() not in _OFFICE_SUFFIXES:
            return request
        hydrated = self._office_document_ingestor.ingest(source.path)
        return replace(
            request,
            requirement_source=replace(
                source,
                text=hydrated.text,
                source_kind=hydrated.source_kind,
                doc_type=hydrated.doc_type or source.doc_type,
            ),
        )

    def _run_cad_ingest(
        self, request: ValidationRequest
    ) -> tuple[tuple[DrawingAnnotation, ...], CapabilityStatus, list[ValidationIssue]]:
        cad_sources = [
            source
            for source in request.drawing_sources
            if source.path is not None
            and (
                source.path.suffix.lower() in _CAD_DRAWING_SUFFIXES
                or (source.format or "").strip().lower() in {"dxf", "dwg", "cad"}
            )
        ]
        if not cad_sources:
            return (
                (),
                CapabilityStatus(
                    CapabilityState.MISSING, "DWG/DXF native analysis not implemented"
                ),
                [],
            )
        if self._cad_model_ingestor is None:
            return (
                (),
                CapabilityStatus(
                    CapabilityState.FAILED,
                    "CAD sources present but CadModelIngestor not configured",
                ),
                [
                    ValidationIssue(
                        rule_id="AEROBIM-CAD-INGEST",
                        severity=Severity.WARNING,
                        message=(
                            "CAD drawing sources present but CadModelIngestor is not configured"
                        ),
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id="cad-ingest",
                    )
                ],
            )

        annotations: list[DrawingAnnotation] = []
        issues: list[ValidationIssue] = []
        saw_dwg = False
        saw_supported_dxf = False
        last_reason: str | None = None
        for source in cad_sources:
            assert source.path is not None
            if source.path.suffix.lower() == ".dwg":
                saw_dwg = True
            result = self._cad_model_ingestor.ingest(source.path, sheet_id=source.sheet_id)
            last_reason = result.reason
            if result.supported:
                saw_supported_dxf = True
                annotations.extend(result.annotations)
            elif result.format_resolved == "dwg":
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-CAD-DWG",
                        severity=Severity.WARNING,
                        message=result.reason or "Native DWG ingest not configured",
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id=str(source.path),
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        rule_id="AEROBIM-CAD-DXF",
                        severity=Severity.WARNING,
                        message=result.reason or "DXF ingest failed",
                        category=FindingCategory.DRAWING_VALIDATION,
                        source_id=str(source.path),
                    )
                )

        if saw_dwg and not saw_supported_dxf:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                last_reason or "Native DWG requires ODA adapter",
            )
        elif saw_supported_dxf:
            # Partial delivery: DXF only — never OK until ODA DWG evidenced.
            capability = CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "DXF ingest via CadModelIngestor (ezdxf); native DWG not verified",
            )
        else:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                last_reason or "CAD ingest produced no supported parse",
            )
        return tuple(annotations), capability, issues

    def _probe_mep_system_graph(self, ifc_path: Path) -> CapabilityStatus:
        if self._mep_system_graph_provider is None:
            return CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "MEP system graph provider not injected",
            )
        try:
            graph = self._mep_system_graph_provider.build(ifc_path)
        except Exception as exc:  # noqa: BLE001 — fail-closed probe
            return CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                str(exc),
            )
        if not graph.nodes:
            return CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "MEP system graph built empty; federated scope still required for sign-off",
            )
        # Still NOT_VERIFIED until customer federated pack (RT-003) — never OK here.
        return CapabilityStatus(
            CapabilityState.NOT_VERIFIED,
            f"MEP graph probe returned {len(graph.nodes)} nodes; customer scope memo pending",
        )

    def _run_quantity_consistency(
        self,
        ifc_path: Path,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        if self._quantity_consistency_checker is None:
            return []
        claims = claims_from_area_requirements(requirements)
        if not claims:
            return []
        try:
            return list(self._quantity_consistency_checker.check(ifc_path, claims))
        except Exception as exc:  # noqa: BLE001
            return [
                ValidationIssue(
                    rule_id="AEROBIM-QTY-ERROR",
                    severity=Severity.WARNING,
                    message=f"Quantity consistency check failed: {exc}",
                    category=FindingCategory.IFC_VALIDATION,
                    source_id="quantity-consistency",
                )
            ]

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
        except Exception as exc:  # noqa: BLE001
            return (
                [
                    ValidationIssue(
                        rule_id="AEROBIM-LOAD-ERROR",
                        severity=Severity.WARNING,
                        message=f"Load evidence verify failed: {exc}",
                        category=FindingCategory.CROSS_DOCUMENT,
                        source_id="load-evidence",
                    )
                ],
                CapabilityStatus(CapabilityState.FAILED, str(exc)),
            )
        mismatches = [i for i in issues if i.rule_id == "AEROBIM-LOAD-MISMATCH"]
        if mismatches:
            capability = CapabilityStatus(
                CapabilityState.FAILED,
                f"{len(mismatches)} load match failure(s)",
            )
        else:
            capability = CapabilityStatus(
                CapabilityState.OK,
                "calculation сверка evaluated (not correctness)",
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
                issues_from_clash_results(results, affects_pass=self._clash_affects_pass),
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
    ) -> ReportCapabilities:
        ifc_validation = (
            CapabilityStatus(CapabilityState.OK)
            if requirements
            else CapabilityStatus(CapabilityState.SKIPPED, "no IFC property requirements")
        )
        unit_scale = CapabilityStatus(CapabilityState.OK)
        for issue in ifc_issues:
            if issue.rule_id == "AEROBIM-UNIT-SCALE":
                unit_scale = CapabilityStatus(
                    CapabilityState.FAILED,
                    issue.message,
                )
                break

        if ids_path is None:
            ids_capability = CapabilityStatus(
                CapabilityState.SKIPPED, "IDS validation not requested"
            )
        elif self._ids_validator is None:
            ids_capability = CapabilityStatus(
                CapabilityState.FAILED, "IDS validation requested but no validator configured"
            )
        elif ids_audit_issues:
            ids_capability = CapabilityStatus(
                CapabilityState.FAILED,
                ids_audit_issues[0].message if ids_audit_issues else "IDS audit failed",
            )
        else:
            ids_capability = CapabilityStatus(CapabilityState.OK)

        if self._ifc_schema_validator is None and schema_request_id is None:
            ifc_schema = CapabilityStatus(
                CapabilityState.SKIPPED, "IFC schema pre-gate not configured"
            )
        elif schema_issues:
            ifc_schema = CapabilityStatus(
                CapabilityState.FAILED,
                schema_issues[0].message if schema_issues else "schema pre-gate failed",
                external_ref=schema_request_id,
            )
        else:
            ifc_schema = CapabilityStatus(
                CapabilityState.OK,
                external_ref=schema_request_id,
            )

        raster_requested = any(
            (source.path and source.path.suffix.lower() in _RASTER_DRAWING_SUFFIXES)
            or (source.format or "").strip().lower() in _RASTER_DRAWING_FORMATS
            for source in drawing_sources
        )
        if not raster_requested:
            raster_capability = CapabilityStatus(
                CapabilityState.SKIPPED, "no raster drawing sources"
            )
        elif self._raster_drawing_analyzer is None:
            raster_capability = CapabilityStatus(
                CapabilityState.SKIPPED, "raster drawing analyzer not configured"
            )
        elif drawing_annotation_count <= 0:
            # Requested OCR path with zero yield must not look like a clean OK.
            raster_capability = CapabilityStatus(
                CapabilityState.FAILED,
                "raster drawing analysis produced zero annotations",
            )
        else:
            raster_capability = CapabilityStatus(CapabilityState.OK)

        return ReportCapabilities(
            clash=clash_capability,
            ids=ids_capability,
            ifc_validation=ifc_validation,
            unit_scale=unit_scale,
            raster=raster_capability,
            ifc_schema=ifc_schema,
            norm_rule_packs=norm_rule_packs
            or CapabilityStatus(CapabilityState.SKIPPED, "norm rule packs not requested"),
            section_pairing=section_pairing
            or CapabilityStatus(CapabilityState.SKIPPED, "PD/RD section pairing not requested"),
            dwg_dxf=dwg_dxf
            or CapabilityStatus(CapabilityState.MISSING, "DWG/DXF native analysis not implemented"),
            mep_system_clash=mep_system_clash
            or CapabilityStatus(
                CapabilityState.NOT_VERIFIED,
                "MEP system graph provider DI-wired but unconfigured (MEP-CLASH-001); "
                "federated MEP IFC + scope memo required",
            ),
            calculation_match=calculation_match
            or CapabilityStatus(CapabilityState.SKIPPED, "numeric calculation match not evaluated"),
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
        if request.ids_path is None or self._ids_document_auditor is None:
            return []
        return list(self._ids_document_auditor.audit(request.ids_path))

    def _collect_ids_issues(self, request: ValidationRequest) -> list[ValidationIssue]:
        if request.ids_path is None:
            return []
        if self._ids_validator is None:
            raise RuntimeError("IDS validation requested but no ids validator is configured")
        return self._ids_validator.validate(request.ids_path, request.ifc_path)

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
        # Precedence: explicit request/manifest paths win; otherwise fall back to
        # the operator-configured env default (AEROBIM_NORM_RULE_PACK). Nothing is
        # hardcoded, and a configured-but-missing default fails closed.
        if request.norm_rule_pack_paths:
            return self._load_norm_packs(
                request.norm_rule_pack_paths, source="request manifest", tolerant=False
            )
        if self._default_norm_rule_pack_path is not None:
            return self._load_norm_packs(
                (self._default_norm_rule_pack_path,),
                source="env AEROBIM_NORM_RULE_PACK",
                tolerant=True,
            )
        return [], CapabilityStatus(CapabilityState.SKIPPED, "norm rule packs not requested")

    def _load_norm_packs(
        self,
        pack_paths: Sequence[Path],
        *,
        source: str,
        tolerant: bool,
    ) -> tuple[list[ParsedRequirement], CapabilityStatus]:
        if self._norm_rule_pack_loader is None:
            raise RuntimeError("Norm rule packs requested but no loader is configured")

        requirements: list[ParsedRequirement] = []
        pack_refs: list[str] = []
        non_approved = False
        seen_packs: set[tuple[str, str]] = set()
        for pack_path in pack_paths:
            try:
                pack = self._norm_rule_pack_loader.load(pack_path)
            except (FileNotFoundError, ValueError, OSError) as exc:
                # Requested or configured packs that fail to load must never look
                # like a clean skip/pass: surface FAILED capability (fail-closed).
                return [], CapabilityStatus(
                    CapabilityState.FAILED,
                    f"norm rule pack unavailable via {source}: {pack_path.name}: {exc}",
                )
            identity = (pack.pack_id, pack.version)
            if identity in seen_packs:
                raise ValueError(
                    f"Duplicate norm rule pack requested: {pack.pack_id}@{pack.version}"
                )
            seen_packs.add(identity)
            requirements.extend(pack.rules)
            if pack.status is not RulePackStatus.APPROVED:
                non_approved = True
            pack_refs.append(
                f"{pack.pack_id}@{pack.version}[{pack.status.value}] sha256:{pack.sha256[:12]}"
            )
        # Ensure every norm-pack rule carries a pack-manifest approval badge.
        stamped: list[ParsedRequirement] = []
        for requirement in requirements:
            if requirement.approval_status is None:
                stamped.append(replace(requirement, approval_status="synthetic"))
            else:
                stamped.append(requirement)
        requirements = stamped
        reason = f"loaded {len(pack_refs)} rule pack(s) via {source}: {', '.join(pack_refs)}"
        if non_approved:
            reason += "; advisory: non-approved pack(s) — not for deterministic sign-off"
        return requirements, CapabilityStatus(CapabilityState.OK, reason)

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
        # Honest capability: unrecognized discipline or zero canonical-key coverage
        # cannot look like a successful pairing.
        if (not report.discipline.recognized) or (
            report.pd_key_count > 0 and report.recognized_key_count == 0
        ):
            return report.issues, CapabilityStatus(CapabilityState.FAILED, reason)
        return report.issues, CapabilityStatus(CapabilityState.OK, reason)

    def _collect_synthesized_requirements(
        self, request: ValidationRequest
    ) -> list[ParsedRequirement]:
        synthesized: list[ParsedRequirement] = []
        for source in (request.technical_spec_source, request.calculation_source):
            if source is None:
                continue
            if not source.text.strip() and source.path is None:
                continue
            synthesized.extend(self._narrative_rule_synthesizer.synthesize(source))
        return synthesized

    def _collect_drawing_annotations(self, request: ValidationRequest) -> list[DrawingAnnotation]:
        annotations: list[DrawingAnnotation] = []
        for drawing_source in request.drawing_sources:
            if self._has_structured_drawing_input(drawing_source):
                annotations.extend(self._drawing_analyzer.analyze(drawing_source))
            if self._is_raster_drawing_source(drawing_source):
                if self._multimodal_drawing_pipeline is not None:
                    result = self._multimodal_drawing_pipeline.analyze(drawing_source, mode="auto")
                    annotations.extend(result.annotations)
                else:
                    annotations.extend(self._collect_raster_annotations(drawing_source))
        return annotations

    def _collect_drawing_assets(self, request: ValidationRequest) -> list[DrawingAsset]:
        assets: list[DrawingAsset] = []
        for index, drawing_source in enumerate(request.drawing_sources, start=1):
            if drawing_source.path is None:
                continue
            suffix = drawing_source.path.suffix.lower()
            if suffix not in _DRAWING_ASSET_SUFFIXES:
                continue
            assets.append(
                DrawingAsset(
                    asset_id=f"drawing-{index:03d}",
                    sheet_id=drawing_source.sheet_id or drawing_source.path.stem.upper(),
                    page_number=1 if suffix != ".pdf" else None,
                    media_type=(
                        "application/pdf"
                        if suffix == ".pdf"
                        else "image/webp"
                        if suffix == ".webp"
                        else "image/jpeg"
                        if suffix in {".jpg", ".jpeg"}
                        else "image/png"
                    ),
                    source_path=drawing_source.path,
                )
            )
        return assets

    def _collect_raster_annotations(
        self,
        drawing_source: DrawingSource,
    ) -> list[DrawingAnnotation]:
        if drawing_source.path is None:
            raise ValueError("Raster drawing analysis requires a drawing file path")
        if self._raster_drawing_analyzer is None:
            raise RuntimeError(
                "Raster drawing analysis requested but no raster drawing analyzer is configured"
            )
        return self._raster_drawing_analyzer.analyze_image(
            drawing_source.path,
            sheet_id=drawing_source.sheet_id,
        )

    def _has_structured_drawing_input(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.text.strip():
            return True
        if drawing_source.path is None:
            return False
        return drawing_source.path.suffix.lower() not in _RASTER_DRAWING_SUFFIXES

    def _collect_identity_sources(self, request: ValidationRequest) -> list[RequirementSource]:
        """Stamp package-level identity onto requirement and drawing sources."""

        sources: list[RequirementSource] = []
        doc_status = request.doc_status
        status_value = doc_status if isinstance(doc_status, str) else None
        for source in (
            request.requirement_source,
            request.technical_spec_source,
            request.calculation_source,
        ):
            if source is None:
                continue
            sources.append(
                stamp_requirement_source(
                    source,
                    revision=source.revision or request.revision,
                    stage=source.stage or request.stage,
                    doc_type=source.doc_type or source.source_kind.value,
                    doc_status=source.doc_status or status_value,
                    source_id=source.source_id or source.source_kind.value,
                )
            )
        for drawing in request.drawing_sources:
            sheet = drawing.sheet_id or (
                drawing.path.name if drawing.path is not None else "drawing"
            )
            sources.append(
                RequirementSource(
                    text=drawing.text,
                    path=drawing.path,
                    source_kind=SourceKind.STRUCTURED_TEXT,
                    source_id=sheet,
                    revision=drawing.revision or request.revision,
                    stage=request.stage,
                    doc_type=drawing.doc_type or "drawing",
                    sha256=drawing.sha256,
                    doc_status=status_value,
                )
            )
        return sources

    def _is_raster_drawing_source(self, drawing_source: DrawingSource) -> bool:
        if drawing_source.format and drawing_source.format.lower() in _RASTER_DRAWING_FORMATS:
            return True
        if drawing_source.path is None:
            return False
        return drawing_source.path.suffix.lower() in _RASTER_DRAWING_SUFFIXES

    def _detect_cross_document_contradictions(
        self,
        requirements: Sequence[ParsedRequirement],
    ) -> list[ValidationIssue]:
        """Compare requirements from different sources for the same (entity, property).

        When two sources specify conflicting expected values for the same
        IFC entity + property pair, emit a CROSS_DOCUMENT issue.  Numeric
        values are compared with ISO 12006-3 ε-tolerance so that rounding
        differences (e.g. 3.0 m vs 3000 mm) do not produce false positives.
        The severity of emitted issues is controlled by ``self._cross_doc_severity``
        (configurable via ``AEROBIM_CROSS_DOC_SEVERITY``).  The ``conflict_kind``
        field classifies the nature of the conflict for downstream policy filtering.
        """
        issues: list[ValidationIssue] = []
        keyed: dict[tuple[str, str, str], list[ParsedRequirement]] = {}

        for req in requirements:
            if not req.ifc_entity or not req.property_name:
                continue
            key = (
                req.ifc_entity.upper(),
                (req.property_set or "").lower(),
                req.property_name.lower(),
            )
            keyed.setdefault(key, []).append(req)

        for (entity, property_set, prop), reqs in keyed.items():
            if len(reqs) < 2:
                continue
            seen: list[ParsedRequirement] = []
            for req in reqs:
                if req.expected_value is None:
                    continue
                for prev_req in seen:
                    if prev_req.source_kind == req.source_kind:
                        continue
                    soft = self._values_soft_conflict(
                        prev_req.expected_value,
                        prev_req.unit,
                        req.expected_value,
                        req.unit,
                        quantity_a=prev_req.quantity,
                        quantity_b=req.quantity,
                    )
                    hard = self._values_conflict(
                        prev_req.expected_value,
                        prev_req.unit,
                        req.expected_value,
                        req.unit,
                        quantity_a=prev_req.quantity,
                        quantity_b=req.quantity,
                    )
                    if not soft and not hard:
                        continue
                    prev_val = (prev_req.expected_value or "").strip()
                    val = (req.expected_value or "").strip()
                    property_label = (
                        f"{entity}.{property_set}.{prop}" if property_set else f"{entity}.{prop}"
                    )
                    if soft and not hard:
                        conflict_kind = ConflictKind.SOFT_CONFLICT_WITHIN_TOLERANCE
                        severity = Severity.INFO
                    else:
                        conflict_kind = self._classify_conflict_kind(
                            prev_req.expected_value,
                            prev_req.unit,
                            req.expected_value,
                            req.unit,
                            quantity_a=prev_req.quantity,
                            quantity_b=req.quantity,
                        )
                        severity = self._cross_doc_severity
                    issues.append(
                        ValidationIssue(
                            rule_id=f"CROSS-DOC-{entity}-{prop}",
                            severity=severity,
                            message=(
                                f"Cross-document contradiction: {property_label} "
                                f"expects '{prev_val}' (from {prev_req.source_kind.value}) "
                                f"but '{val}' (from {req.source_kind.value})"
                            ),
                            ifc_entity=entity,
                            category=FindingCategory.CROSS_DOCUMENT,
                            property_set=prev_req.property_set or req.property_set,
                            property_name=prop,
                            expected_value=prev_val,
                            observed_value=val,
                            conflict_kind=conflict_kind,
                        )
                    )
                seen.append(req)

        return issues

    def _resolve_quantity(
        self,
        value: str | None,
        unit: str | None,
        quantity: QuantityValue | None,
    ) -> QuantityValue | None:
        if quantity is not None and quantity.si_value is not None:
            return quantity
        if value is None:
            return None
        numeric = self._to_float(value.strip())
        if numeric is None:
            return None
        return parse_quantity(numeric, unit or "")

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
        """Classify a detected cross-document conflict into a ``ConflictKind``.

        Decision order:
        1. UNIT_MISMATCH — same dimensionality but inconsistent unit encoding.
        2. HARD_CONFLICT — values differ after full SI normalisation.
        3. AMBIGUOUS_MAPPING — non-numeric values with no unit context.
        """
        if value_a is None or value_b is None:
            return ConflictKind.AMBIGUOUS_MAPPING

        q_a = self._resolve_quantity(value_a, unit_a, quantity_a)
        q_b = self._resolve_quantity(value_b, unit_b, quantity_b)

        if (
            q_a is not None
            and q_b is not None
            and q_a.si_value is not None
            and q_b.si_value is not None
        ):
            if q_a.ucum_code and q_b.ucum_code:
                if q_a.dimension != q_b.dimension:
                    return ConflictKind.UNIT_MISMATCH
                return ConflictKind.HARD_CONFLICT
            if unit_a and unit_b and unit_a.strip().lower() != unit_b.strip().lower():
                return ConflictKind.UNIT_MISMATCH
            return ConflictKind.HARD_CONFLICT

        a_num = self._to_float(value_a.strip())
        b_num = self._to_float(value_b.strip())
        if a_num is not None and b_num is not None:
            if unit_a and unit_b and unit_a.strip().lower() != unit_b.strip().lower():
                return ConflictKind.UNIT_MISMATCH
            return ConflictKind.HARD_CONFLICT

        return ConflictKind.HARD_CONFLICT

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
        if value_a is None or value_b is None:
            return False
        a_str = value_a.strip()
        b_str = value_b.strip()
        if a_str.lower() == b_str.lower():
            return False
        # Unit-normalized equivalence (1 m vs 1000 mm) is not a soft conflict.
        unit_a_norm = (unit_a or "").strip().lower()
        unit_b_norm = (unit_b or "").strip().lower()
        if unit_a_norm and unit_b_norm and unit_a_norm != unit_b_norm:
            return False
        if self._values_conflict(
            value_a,
            unit_a,
            value_b,
            unit_b,
            quantity_a=quantity_a,
            quantity_b=quantity_b,
        ):
            return False

        a_num = self._to_float(a_str)
        b_num = self._to_float(b_str)
        return a_num is not None and b_num is not None and a_num != b_num

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
        if value_a is None or value_b is None:
            return False
        a_str = value_a.strip()
        b_str = value_b.strip()
        if a_str.lower() == b_str.lower():
            return False

        q_a = self._resolve_quantity(value_a, unit_a, quantity_a)
        q_b = self._resolve_quantity(value_b, unit_b, quantity_b)
        if (
            q_a is not None
            and q_b is not None
            and q_a.si_value is not None
            and q_b.si_value is not None
            and q_a.ucum_code
            and q_b.ucum_code
        ):
            if q_a.dimension != q_b.dimension:
                return True
            eps = self._tolerance.epsilon_for_unit(q_a.ucum_code)
            return not si_compare(q_a, q_b, epsilon=eps)

        a_num = self._to_float(a_str)
        b_num = self._to_float(b_str)
        if a_num is not None and b_num is not None:
            parsed_a = parse_quantity(a_num, unit_a or "")
            parsed_b = parse_quantity(b_num, unit_b or "")
            if parsed_a.ucum_code and parsed_b.ucum_code:
                if parsed_a.dimension != parsed_b.dimension:
                    return True
                eps = self._tolerance.epsilon_for_unit(parsed_a.ucum_code)
                return not si_compare(parsed_a, parsed_b, epsilon=eps)

            eps = self._tolerance.epsilon_for_unit(unit_a or unit_b or "")
            return abs(a_num - b_num) > eps

        return True

    def _normalize_cross_document_numeric_value(
        self,
        value: float,
        unit: str | None,
    ) -> tuple[float, str] | None:
        if unit is None:
            return None
        normalized = _CROSS_DOC_UNIT_TO_SI_FACTOR.get(unit.strip().lower())
        if normalized is None:
            return None
        canonical_unit, factor = normalized
        return value * factor, canonical_unit

    def _validate_drawing_annotations(
        self,
        requirements: Sequence[ParsedRequirement],
        drawing_annotations: Sequence[DrawingAnnotation],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        drawing_requirements = [
            requirement
            for requirement in requirements
            if requirement.rule_scope is RuleScope.DRAWING_ANNOTATION
        ]

        for requirement in drawing_requirements:
            matching_annotations = [
                annotation
                for annotation in drawing_annotations
                if self._matches_annotation(requirement, annotation)
            ]
            if not matching_annotations:
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message="No drawing annotations matched the normalized rule",
                        category=FindingCategory.DRAWING_VALIDATION,
                    )
                )
                continue

            for annotation in matching_annotations:
                if self._compare_values(
                    annotation.observed_value,
                    requirement.expected_value,
                    requirement.operator,
                    unit=requirement.unit or annotation.unit,
                ):
                    continue
                issues.append(
                    issue_from_requirement(
                        requirement,
                        severity=Severity.ERROR,
                        message="Drawing annotation does not match the normalized rule",
                        category=FindingCategory.DRAWING_VALIDATION,
                        target_ref=annotation.target_ref,
                        observed_value=annotation.observed_value,
                        problem_zone=annotation.problem_zone,
                        unit=requirement.unit or annotation.unit,
                    )
                )

        return issues

    def _attach_remarks(self, issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
        enriched: list[ValidationIssue] = []
        for issue in issues:
            enriched.append(replace(issue, remark=self._remark_generator.generate(issue)))
        return enriched

    def _matches_annotation(
        self, requirement: ParsedRequirement, annotation: DrawingAnnotation
    ) -> bool:
        if (
            requirement.target_ref
            and requirement.target_ref.lower() != annotation.target_ref.lower()
        ):
            return False
        if (
            requirement.property_name
            and requirement.property_name.lower() != annotation.measure_name.lower()
        ):
            return False
        if requirement.instructions and requirement.instructions.startswith("sheet="):
            expected_sheet = requirement.instructions.split("=", maxsplit=1)[1].strip().lower()
            if annotation.sheet_id.lower() != expected_sheet:
                return False
        return True

    def _compare_values(
        self,
        observed_value: str | None,
        expected_value: str | None,
        operator: ComparisonOperator,
        unit: str | None = None,
    ) -> bool:
        """Compare observed vs expected using fuzzy ε-tolerance for numerics.

        ISO 12006-3 aligned: exact float equality is replaced with
        ``abs(a - b) <= ε`` where ε depends on the measurement unit.
        This eliminates false positives from millimetre-level rounding
        differences that are inevitable in real BIM data.
        """
        if operator is ComparisonOperator.EXISTS:
            return observed_value is not None
        if observed_value is None or expected_value is None:
            return False

        observed_number = self._to_float(observed_value)
        expected_number = self._to_float(expected_value)

        if observed_number is not None and expected_number is not None:
            observed_q = parse_quantity(observed_number, unit or "")
            expected_q = parse_quantity(expected_number, unit or "")
            if (
                observed_q.ucum_code
                and expected_q.ucum_code
                and observed_q.dimension == expected_q.dimension
                and observed_q.si_value is not None
                and expected_q.si_value is not None
            ):
                # ToleranceConfig ε is expressed in the declared unit; scale to SI.
                eps_native = self._tolerance.epsilon_for_unit(unit)
                scale = abs(observed_q.si_value / observed_number) if observed_number else 1.0
                eps_si = eps_native * scale
                if operator is ComparisonOperator.GREATER_OR_EQUAL:
                    return observed_q.si_value >= expected_q.si_value - eps_si
                if operator is ComparisonOperator.LESS_OR_EQUAL:
                    return observed_q.si_value <= expected_q.si_value + eps_si
                return si_compare(observed_q, expected_q, epsilon=eps_si)

            eps = self._tolerance.epsilon_for_unit(unit)
            if operator is ComparisonOperator.GREATER_OR_EQUAL:
                return observed_number >= expected_number - eps
            if operator is ComparisonOperator.LESS_OR_EQUAL:
                return observed_number <= expected_number + eps
            # EQUALS with tolerance band
            return abs(observed_number - expected_number) <= eps

        # Non-numeric fallback: exact string comparison
        if operator in {ComparisonOperator.GREATER_OR_EQUAL, ComparisonOperator.LESS_OR_EQUAL}:
            return observed_value == expected_value
        return observed_value == expected_value

    def _to_float(self, raw: str) -> float | None:
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None
