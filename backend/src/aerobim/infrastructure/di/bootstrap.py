from __future__ import annotations

import json
from pathlib import Path

from aerobim.application.services.agentic_review_orchestrator import AgenticReviewOrchestrator
from aerobim.application.services.compliance_agent_orchestrator import ComplianceAgentOrchestrator
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
    GetAnalyzeProjectPackageJobStatusUseCase,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.application.use_cases.apply_norm_rule_hitl_event import ApplyNormRuleHitlEventUseCase
from aerobim.application.use_cases.compile_requirements_to_ids import (
    CompileRequirementsToIdsUseCase,
)
from aerobim.application.use_cases.push_report_to_bcf_api import PushReportToBcfApiUseCase
from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import resolve_storage_path
from aerobim.domain.hybrid.model_router import ModelRouter, ProviderRegistry
from aerobim.domain.models import Severity, ToleranceConfig
from aerobim.domain.pdf_backend import resolve_pdf_backend
from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.bsi_validation_service import (
    HttpBsiValidationService,
    LocalSchemaPackCertificate,
)
from aerobim.infrastructure.adapters.deterministic_requirement_interpreter import (
    DeterministicRequirementInterpreter,
)
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)
from aerobim.infrastructure.adapters.disabled_pdf_extraction_integrity_producer import (
    DisabledPdfExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.docling_office_document_ingestor import (
    DoclingOfficeDocumentIngestor,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.ezdxf_cad_entity_loader import EzdxfCadEntityLoader
from aerobim.infrastructure.adapters.ezdxf_cad_model_ingestor import EzdxfCadModelIngestor
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.filesystem_norm_corpus_retriever import (
    FilesystemNormCorpusRetriever,
)
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.infrastructure.adapters.http_bcf_api_client import HttpBcfApiClient
from aerobim.infrastructure.adapters.hybrid_drawing_analyzer import HybridDrawingAnalyzer
from aerobim.infrastructure.adapters.ifc_aabb_mep_pair_filter import IfcAabbMepPairFilter
from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from aerobim.infrastructure.adapters.ifc_quantity_consistency_adapter import (
    IfcQuantityConsistencyAdapter,
)
from aerobim.infrastructure.adapters.ifc_system_aware_clash import IfcSystemAwareClash
from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.json_detached_signature_auditor import (
    JsonDetachedSignatureAuditor,
)
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
from aerobim.infrastructure.adapters.json_package_inventory_loader import (
    JsonPackageInventoryLoader,
)
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer
from aerobim.infrastructure.adapters.json_structured_logger import JsonStructuredLogger
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.manifest_logic_consistency_adapter import (
    ManifestLogicConsistencyAdapter,
)
from aerobim.infrastructure.adapters.multimodal_drawing_analyzer_port import (
    MultimodalDrawingAnalyzerPort,
)
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.object_store_norm_pack_version_store import (
    ObjectStoreNormRulePackVersionStore,
)
from aerobim.infrastructure.adapters.ocr_aware_extraction_integrity_producer import (
    OcrAwareExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.ocr_fallback_multimodal_drawing_pipeline import (
    OcrFallbackMultimodalDrawingPipeline,
)
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import OpenRebarEvidenceVerifier
from aerobim.infrastructure.adapters.pdfium_region_cropper import PdfiumRegionCropper
from aerobim.infrastructure.adapters.postgres_audit_store import PostgresAuditStore
from aerobim.infrastructure.adapters.pymupdf_extraction_integrity_producer import (
    PyMuPDFExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper
from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import (
    RedisAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)
from aerobim.infrastructure.adapters.relational_ifc_knowledge_graph import (
    RelationalIfcKnowledgeGraph,
)
from aerobim.infrastructure.adapters.s3_object_store import S3ObjectStore
from aerobim.infrastructure.adapters.scoped_mep_system_graph_provider import (
    ScopedMepSystemGraphProvider,
)
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.adapters.unconfigured_bcf_api_client import UnconfiguredBcfApiClient
from aerobim.infrastructure.adapters.unconfigured_system_clash import UnconfiguredSystemClash
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.infrastructure.security.oidc_token_validator import OidcTokenValidator


def bootstrap_container(settings: Settings | None = None) -> Container:
    container = Container()
    runtime_settings = settings or Settings.from_env()
    runtime_settings.require_secure_auth()
    runtime_settings.storage_dir.mkdir(parents=True, exist_ok=True)

    from aerobim.infrastructure.adapters.ifc_file_open import configure_ifc_parse_cache

    configure_ifc_parse_cache(runtime_settings.ifc_parse_cache_dir)

    container.register(Tokens.SETTINGS, lambda _container: runtime_settings)
    container.register(
        Tokens.LOGGER,
        lambda _container: JsonStructuredLogger(name="aerobim"),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REQUIREMENT_EXTRACTOR,
        lambda _container: StructuredRequirementExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NARRATIVE_RULE_SYNTHESIZER,
        lambda _container: NarrativeRuleSynthesizer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NORM_RULE_PACK_LOADER,
        lambda _container: JsonNormRulePackLoader(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SECTION_DIFF_ANALYZER,
        lambda _container: JsonSectionDiffAnalyzer(
            tolerance=tolerance,
            severity=Severity(
                runtime_settings.cross_doc_contradiction_severity
                if runtime_settings.cross_doc_contradiction_severity in {"error", "warning", "info"}
                else "warning"
            ),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER,
        lambda _container: StructuredDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.RASTER_DRAWING_ANALYZER,
        lambda _container: RasterDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.EXTRACTION_INTEGRITY_PRODUCER,
        lambda current: _build_extraction_integrity_producer(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DOCUMENT_SIGNATURE_AUDITOR,
        lambda _container: JsonDetachedSignatureAuditor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.PACKAGE_INVENTORY_LOADER,
        lambda _container: JsonPackageInventoryLoader(),
        lifecycle=Lifecycle.SINGLETON,
    )
    tolerance = ToleranceConfig()
    container.register(
        Tokens.IFC_VALIDATOR,
        lambda _container: IfcOpenShellValidator(tolerance=tolerance),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IDS_VALIDATOR,
        lambda _container: IfcTesterIdsValidator(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IFC_SCHEMA_VALIDATOR,
        lambda _container: BasicIfcSchemaValidator(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IDS_DOCUMENT_AUDITOR,
        lambda _container: XmlIdsDocumentAuditor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CLASH_DETECTOR,
        lambda _container: IfcClashDetector(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MEP_SYSTEM_GRAPH_PROVIDER,
        lambda current: ScopedMepSystemGraphProvider(
            scope_path=_resolve_mep_federated_scope_path(current.resolve(Tokens.SETTINGS)),
            repo_root=Path(__file__).resolve().parents[5],
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MEP_AABB_PAIR_FILTER,
        lambda _container: IfcAabbMepPairFilter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CAD_MODEL_INGESTOR,
        lambda _container: EzdxfCadModelIngestor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.OFFICE_DOCUMENT_INGESTOR,
        lambda _container: DoclingOfficeDocumentIngestor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DETERMINISM_GATE,
        lambda _container: DeterminismGate(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.QUANTITY_CONSISTENCY_CHECKER,
        lambda _container: IfcQuantityConsistencyAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.LOAD_EVIDENCE_VERIFIER,
        lambda _container: SpreadsheetLoadEvidenceAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.LOGIC_CONSISTENCY_ANALYZER,
        lambda _container: ManifestLogicConsistencyAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_REGION_DETECTOR,
        lambda _container: HeuristicLayoutRegionDetector(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MULTIMODAL_DRAWING_PIPELINE,
        lambda current: OcrFallbackMultimodalDrawingPipeline(
            raster_analyzer=current.resolve(Tokens.RASTER_DRAWING_ANALYZER),
            region_detector=current.resolve(Tokens.DRAWING_REGION_DETECTOR),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Advisory VLM (§3/§7): available under kimi_advisory_ready(), but DELIBERATELY
    # NOT consumed by AnalyzeProjectPackageUseCase — its candidate regions must
    # never reach engine_issues / summary.passed (advisory OFF==ON invariant).
    container.register(
        Tokens.ADVISORY_VLM_PIPELINE,
        lambda current: _build_advisory_vlm_pipeline(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Hybrid AI fail-closed pre-gate (WP-02): classify -> policy -> (mask) -> audit.
    # Consumed by AdvisoryOrchestrator as a mandatory pre-gate (not by the verdict path).
    # Registered mask-less (no PrivacyGuard) by default: external egress of a payload
    # stays fail-closed (masked=None -> may_call_external=False) until a deployment
    # injects a tenant-scoped PrivacyGuard.
    container.register(
        Tokens.HYBRID_ROUTE_GATE,
        lambda _container: HybridRouteGate(),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Hybrid AI model router (P2): AVAILABLE + config-driven, but NOT on the verdict path.
    # Default registry is local-only (fail-closed): private/public tiers require a
    # deployment-provided provider config, so there is no external egress by default.
    container.register(
        Tokens.HYBRID_MODEL_ROUTER,
        lambda current: _build_model_router(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Fail LOUD at boot (not lazily) when a provider config is set: resolve now so a
    # missing/invalid config raises during bootstrap, not on some later first use.
    if runtime_settings.hybrid_provider_config_path:
        container.resolve(Tokens.HYBRID_MODEL_ROUTER)
    container.register(
        Tokens.REQUIREMENT_TO_IDS_COMPILER,
        lambda current: DeterministicRequirementToIdsCompiler(
            requirement_extractor=current.resolve(Tokens.REQUIREMENT_EXTRACTOR)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NORM_CORPUS_RETRIEVER,
        lambda current: FilesystemNormCorpusRetriever(
            corpus_roots=_default_norm_corpus_roots(current.resolve(Tokens.SETTINGS))
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.COMPILE_REQUIREMENTS_TO_IDS_USE_CASE,
        lambda current: CompileRequirementsToIdsUseCase(
            compiler=current.resolve(Tokens.REQUIREMENT_TO_IDS_COMPILER),
            norm_retriever=current.resolve(Tokens.NORM_CORPUS_RETRIEVER),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ODA_CAD_MODEL_INGESTOR,
        lambda current: OdaCadModelIngestor(
            enabled=current.resolve(Tokens.SETTINGS).oda_cad_enabled
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IFC_KNOWLEDGE_GRAPH,
        lambda _container: RelationalIfcKnowledgeGraph(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SYSTEM_CLASH,
        lambda current: _build_system_clash(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REQUIREMENT_INTERPRETER,
        lambda current: DeterministicRequirementInterpreter(
            compiler=current.resolve(Tokens.REQUIREMENT_TO_IDS_COMPILER)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CAD_ENTITY_LOADER,
        lambda _container: EzdxfCadEntityLoader(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER_PORT,
        lambda current: _build_drawing_analyzer_port(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.COMPLIANCE_AGENT_ORCHESTRATOR,
        lambda current: ComplianceAgentOrchestrator(
            norm_retriever=current.resolve(Tokens.NORM_CORPUS_RETRIEVER),
            ids_compiler=current.resolve(Tokens.REQUIREMENT_TO_IDS_COMPILER),
            load_verifier=current.resolve(Tokens.LOAD_EVIDENCE_VERIFIER),
            logic_analyzer=current.resolve(Tokens.LOGIC_CONSISTENCY_ANALYZER),
            quantity_checker=current.resolve(Tokens.QUANTITY_CONSISTENCY_CHECKER),
            clash_detector=current.resolve(Tokens.CLASH_DETECTOR),
            ifc_knowledge_graph=current.resolve(Tokens.IFC_KNOWLEDGE_GRAPH),
            system_clash=current.resolve(Tokens.SYSTEM_CLASH),
            max_steps=8,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.AGENTIC_REVIEW_ORCHESTRATOR,
        lambda current: AgenticReviewOrchestrator(
            compliance_agent=current.resolve(Tokens.COMPLIANCE_AGENT_ORCHESTRATOR)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.EXTERNAL_EVIDENCE_VERIFIER,
        lambda _container: OpenRebarEvidenceVerifier(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REMARK_GENERATOR,
        lambda current: TemplateRemarkGenerator(
            locale=current.resolve(Tokens.SETTINGS).remark_locale
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.OBJECT_STORE,
        lambda current: _build_object_store(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.AUDIT_REPORT_STORE,
        lambda current: _build_audit_report_store(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE,
        lambda current: _build_job_store(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.BCF_API_CLIENT,
        lambda current: _build_bcf_api_client(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.OIDC_TOKEN_VALIDATOR,
        lambda current: _build_oidc_validator(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    bsi_service = _build_bsi_validation_service(runtime_settings)
    if bsi_service is not None:
        registered_bsi = bsi_service

        def _resolve_bsi(_container: Container):
            return registered_bsi

        container.register(
            Tokens.BSI_VALIDATION_SERVICE,
            _resolve_bsi,
            lifecycle=Lifecycle.SINGLETON,
        )
    container.register(
        Tokens.REVIEW_EVENT_STORE,
        lambda current: FilesystemReviewEventStore(
            current.resolve(Tokens.SETTINGS).storage_dir,
            fail_closed=current.resolve(Tokens.SETTINGS).audit_fail_closed,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NORM_RULE_PACK_VERSION_STORE,
        lambda current: ObjectStoreNormRulePackVersionStore(
            current.resolve(Tokens.OBJECT_STORE),
            index_dir=current.resolve(Tokens.SETTINGS).storage_dir,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.APPLY_NORM_RULE_HITL_EVENT_USE_CASE,
        lambda current: ApplyNormRuleHitlEventUseCase(
            version_store=current.resolve(Tokens.NORM_RULE_PACK_VERSION_STORE),
            review_event_store=current.resolve(Tokens.REVIEW_EVENT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE,
        lambda current: PushReportToBcfApiUseCase(
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            bcf_api_client=current.resolve(Tokens.BCF_API_CLIENT),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
        lambda current: ValidateIfcAgainstIdsUseCase(
            requirement_extractor=current.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            ifc_validator=current.resolve(Tokens.IFC_VALIDATOR),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            ids_validator=current.resolve(Tokens.IDS_VALIDATOR),
            ifc_schema_validator=current.resolve(Tokens.IFC_SCHEMA_VALIDATOR),
            ids_document_auditor=current.resolve(Tokens.IDS_DOCUMENT_AUDITOR),
            signoff_profile=current.resolve(Tokens.SETTINGS).signoff_profile,
            require_clash=current.resolve(Tokens.SETTINGS).require_clash,
            clash_affects_pass=current.resolve(Tokens.SETTINGS).clash_affects_pass,
            require_bsi_schema=current.resolve(Tokens.SETTINGS).require_bsi_schema,
            require_mep_system_clash=current.resolve(Tokens.SETTINGS).require_mep_system_clash,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
        lambda current: AnalyzeProjectPackageUseCase(
            requirement_extractor=current.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            narrative_rule_synthesizer=current.resolve(Tokens.NARRATIVE_RULE_SYNTHESIZER),
            drawing_analyzer=current.resolve(Tokens.DRAWING_ANALYZER),
            ifc_validator=current.resolve(Tokens.IFC_VALIDATOR),
            ids_validator=current.resolve(Tokens.IDS_VALIDATOR),
            raster_drawing_analyzer=current.resolve(Tokens.RASTER_DRAWING_ANALYZER),
            remark_generator=current.resolve(Tokens.REMARK_GENERATOR),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            tolerance=tolerance,
            clash_detector=current.resolve(Tokens.CLASH_DETECTOR),
            cross_doc_severity=current.resolve(Tokens.SETTINGS).cross_doc_contradiction_severity,
            priority_profile=current.resolve(Tokens.SETTINGS).priority_profile,
            external_evidence_verifier=current.resolve(Tokens.EXTERNAL_EVIDENCE_VERIFIER),
            clash_affects_pass=current.resolve(Tokens.SETTINGS).clash_affects_pass,
            require_clash=current.resolve(Tokens.SETTINGS).require_clash,
            require_bsi_schema=current.resolve(Tokens.SETTINGS).require_bsi_schema,
            require_mep_system_clash=current.resolve(Tokens.SETTINGS).require_mep_system_clash,
            signoff_profile=current.resolve(Tokens.SETTINGS).signoff_profile,
            ifc_schema_validator=current.resolve(Tokens.IFC_SCHEMA_VALIDATOR),
            ids_document_auditor=current.resolve(Tokens.IDS_DOCUMENT_AUDITOR),
            bsi_validation_service=(
                current.resolve(Tokens.BSI_VALIDATION_SERVICE)
                if current.is_registered(Tokens.BSI_VALIDATION_SERVICE)
                else None
            ),
            norm_rule_pack_loader=current.resolve(Tokens.NORM_RULE_PACK_LOADER),
            section_diff_analyzer=current.resolve(Tokens.SECTION_DIFF_ANALYZER),
            default_norm_rule_pack_path=_resolve_default_norm_pack_path(
                current.resolve(Tokens.SETTINGS)
            ),
            cad_model_ingestor=current.resolve(Tokens.CAD_MODEL_INGESTOR),
            office_document_ingestor=current.resolve(Tokens.OFFICE_DOCUMENT_INGESTOR),
            mep_system_graph_provider=current.resolve(Tokens.MEP_SYSTEM_GRAPH_PROVIDER),
            determinism_gate=current.resolve(Tokens.DETERMINISM_GATE),
            quantity_consistency_checker=current.resolve(Tokens.QUANTITY_CONSISTENCY_CHECKER),
            load_evidence_verifier=current.resolve(Tokens.LOAD_EVIDENCE_VERIFIER),
            logic_consistency_analyzer=current.resolve(Tokens.LOGIC_CONSISTENCY_ANALYZER),
            multimodal_drawing_pipeline=current.resolve(Tokens.MULTIMODAL_DRAWING_PIPELINE),
            compliance_agent=current.resolve(Tokens.COMPLIANCE_AGENT_ORCHESTRATOR),
            review_event_store=current.resolve(Tokens.REVIEW_EVENT_STORE),
            mep_federated_scope_path=_resolve_mep_federated_scope_path(
                current.resolve(Tokens.SETTINGS)
            ),
            mep_aabb_pair_filter=current.resolve(Tokens.MEP_AABB_PAIR_FILTER),
            mep_aabb_filter_enabled=current.resolve(Tokens.SETTINGS).mep_aabb_filter_enabled,
            extraction_integrity_producer=current.resolve(Tokens.EXTRACTION_INTEGRITY_PRODUCER),
            hybrid_route_gate=current.resolve(Tokens.HYBRID_ROUTE_GATE),
            document_signature_auditor=current.resolve(Tokens.DOCUMENT_SIGNATURE_AUDITOR),
            package_inventory_loader=current.resolve(Tokens.PACKAGE_INVENTORY_LOADER),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE,
        lambda current: SubmitAnalyzeProjectPackageJobUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE,
        lambda current: GetAnalyzeProjectPackageJobStatusUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER,
        lambda current: AnalyzeProjectPackageJobRunner(
            analyze_use_case=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE),
            job_store=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE),
            logger=current.resolve(Tokens.LOGGER),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    return container


def _resolve_mep_federated_scope_path(settings: Settings) -> Path | None:
    raw = settings.mep_federated_scope_path
    if not raw:
        return None
    from aerobim.core.security.path_jail import PathJailError, resolve_repo_relative_path

    repo_root = Path(__file__).resolve().parents[5]
    try:
        return resolve_repo_relative_path(raw, repo_root=repo_root)
    except PathJailError:
        # Absolute env paths are operator-local only when already under repo_root.
        path = Path(raw)
        if path.is_absolute():
            resolved = path.resolve()
            if resolved.is_relative_to(repo_root.resolve()):
                return resolved
        raise


def _resolve_default_norm_pack_path(settings: Settings) -> Path | None:
    """Resolve the operator-configured default norm pack within the storage jail.

    Existence is intentionally tolerated here: a configured-but-missing pack is
    surfaced at analysis time as a FAILED ``norm_rule_packs`` capability (fail
    closed, never a silent skip). Traversal/symlink/absolute paths still raise.
    """
    if not settings.norm_rule_pack_path:
        return None
    return resolve_storage_path(settings.norm_rule_pack_path, base=settings.storage_dir)


def _default_norm_corpus_roots(settings: Settings) -> list[Path]:
    """Local corpus roots for keyword NormCorpusRetriever (advisory)."""

    repo_root = Path(__file__).resolve().parents[5]
    roots = [
        settings.storage_dir / "norm-corpus",
        repo_root / "samples" / "tz-appendix" / "03-standards",
        repo_root / "samples" / "specifications",
        repo_root / "samples" / "requirements",
    ]
    return [path for path in roots if path.exists()] or [settings.storage_dir / "norm-corpus"]


def _build_object_store(settings: Settings):
    if settings.s3_bucket:
        try:
            return S3ObjectStore(
                bucket=settings.s3_bucket,
                region=settings.s3_region,
                endpoint_url=settings.s3_endpoint_url,
                access_key_id=settings.s3_access_key_id,
                secret_access_key=settings.s3_secret_access_key,
                prefix=settings.s3_prefix,
                allow_http_endpoint=settings.is_dev_environment,
                max_get_bytes=settings.max_ifc_bytes,
            )
        except RuntimeError:
            # Production / pilot: never hide enterprise object-store failure behind local FS.
            if not settings.is_dev_environment or settings.signoff_profile in {
                "samolet_pilot",
                "production",
            }:
                raise
            return LocalObjectStore(
                settings.storage_dir,
                max_get_bytes=settings.max_ifc_bytes,
            )
    return LocalObjectStore(
        settings.storage_dir,
        max_get_bytes=settings.max_ifc_bytes,
    )


def _build_job_store(settings: Settings):
    if settings.redis_url:
        try:
            return RedisAnalyzeProjectPackageJobStore(settings.redis_url)
        except RuntimeError:
            if not settings.is_dev_environment:
                raise
    return InMemoryAnalyzeProjectPackageJobStore(
        snapshot_path=settings.storage_dir / "analyze_project_package_jobs.snapshot.json"
    )


def _build_bcf_api_client(settings: Settings):
    if settings.bcf_api_base_url and settings.bcf_api_token:
        return HttpBcfApiClient(
            base_url=settings.bcf_api_base_url,
            access_token=settings.bcf_api_token,
            api_version=settings.bcf_api_version,
        )
    return UnconfiguredBcfApiClient()


_DEFAULT_MODEL_ROUTER_CONFIG = {
    "profiles": {
        "local_default": {"tier": "local", "provider": "onprem", "model_id": "local-default"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "expert"},
    },
    "tier_defaults": {"local": "local_default"},
    "human_review_profile": "human_review",
}


def _build_model_router(settings: Settings) -> ModelRouter:
    """Hybrid AI model router from deployment config, else LOCAL-ONLY fail-closed.

    A configured provider-config path that is missing/invalid fails closed LOUD
    (RuntimeError) rather than silently enabling or disabling external tiers.
    """
    path = settings.hybrid_provider_config_path
    if not path:
        return ModelRouter(ProviderRegistry.from_config(_DEFAULT_MODEL_ROUTER_CONFIG))
    config_path = Path(path)
    if not config_path.is_file():
        raise RuntimeError(f"AEROBIM_HYBRID_PROVIDER_CONFIG not found: {path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("profiles"):
            raise ValueError("provider config has no 'profiles'")
        return ModelRouter(ProviderRegistry.from_config(data))
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RuntimeError(f"invalid hybrid provider config {path!r}: {exc}") from exc


def _build_oidc_validator(settings: Settings) -> OidcTokenValidator | None:
    if not settings.oidc_enabled:
        return None
    # Defense-in-depth: never gate a security-config invariant on `assert` (it is
    # stripped under `python -O`). `oidc_enabled` already implies all three are set,
    # but an explicit guard stays fail-closed under -O and any future refactor of
    # the property, refusing to build a validator with partial config.
    if not (settings.oidc_issuer and settings.oidc_audience and settings.oidc_jwks_url):
        raise RuntimeError(
            "OIDC enabled but issuer/audience/jwks_url incomplete; refusing to build "
            "an OIDC validator with partial security config"
        )
    return OidcTokenValidator(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        jwks_url=settings.oidc_jwks_url,
    )


def _build_bsi_validation_service(settings: Settings):
    if settings.bsi_validation_url and settings.bsi_api_token:
        return HttpBsiValidationService(
            base_url=settings.bsi_validation_url,
            api_token=settings.bsi_api_token,
        )
    if settings.bsi_local_cert:
        return LocalSchemaPackCertificate()
    return None


def _build_system_clash(settings: Settings):
    if settings.mep_system_clash_enabled:
        return IfcSystemAwareClash(
            enabled=True,
            scope_memo_ref=settings.mep_scope_memo_ref,
        )
    return UnconfiguredSystemClash()


def _build_drawing_analyzer_port(current: Container):
    settings = current.resolve(Tokens.SETTINGS)
    if settings.hybrid_drawing_enabled:
        return HybridDrawingAnalyzer(
            raster_analyzer=current.resolve(Tokens.RASTER_DRAWING_ANALYZER),
            region_detector=current.resolve(Tokens.DRAWING_REGION_DETECTOR),
        )
    return MultimodalDrawingAnalyzerPort(
        pipeline=current.resolve(Tokens.MULTIMODAL_DRAWING_PIPELINE)
    )


_CACHE_NAMESPACE_ALLOWED = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)


def _safe_cache_namespace(value: str | None) -> str | None:
    """Validated tenant/project cache scope, or None (fail-closed) (§5).

    Rejects empty / oversized / path-unsafe values so a namespace can never
    traverse the cache root (``..``, separators) or be silently blank. Callers
    treat None as “do not build a persistent cache” rather than sharing one.
    """
    candidate = (value or "").strip()
    if not (1 <= len(candidate) <= 64) or candidate in {".", ".."}:
        return None
    if any(ch not in _CACHE_NAMESPACE_ALLOWED for ch in candidate):
        return None
    return candidate


def _build_advisory_vlm_pipeline(current: Container) -> RegionRestrictedVlmPipeline:
    """Region-restricted advisory VLM; fail-closed and NOT on the verdict path.

    Constructed ready only when ``settings.kimi_advisory_ready()`` (opt-in, and
    hard-disabled on samolet_pilot / production). Even when ready it is not wired
    into the deterministic use case, so toggling the flag cannot change
    ``summary.passed`` (advisory OFF==ON). A future advisory surface may consume
    it, but must keep candidate regions out of ``engine_issues``.
    """
    settings = current.resolve(Tokens.SETTINGS)
    if not settings.kimi_advisory_ready():
        return RegionRestrictedVlmPipeline(
            region_detector=None, reader=None, cropper=None, ready=False
        )
    from aerobim.infrastructure.adapters.kimi_k3_advisory_client import VlmAdvisoryClient

    client = VlmAdvisoryClient(
        base_url=settings.kimi_api_base_url or "",
        api_key=settings.kimi_api_key or "",
        model=settings.kimi_model,
        reasoning_effort=settings.kimi_reasoning_effort,
    )
    # §2.1/§5: deterministic act-grade replay ONLY with a trusted tenant scope.
    # The pipeline is a process singleton with no per-request identity, so a
    # persistent cache without a validated namespace could replay one tenant's
    # response for another. Fail closed: no namespace -> no persistent cache.
    reader: object = client
    cache_namespace = _safe_cache_namespace(settings.kimi_cache_namespace)
    # A configured-but-invalid project fails closed (None); unset project -> "".
    cache_project = (
        _safe_cache_namespace(settings.kimi_cache_project) if settings.kimi_cache_project else ""
    )
    if settings.kimi_cache_dir and cache_namespace and cache_project is not None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import (
            CachingVlmReader,
            FilesystemVlmResponseStore,
        )
        from aerobim.infrastructure.adapters.kimi_k3_advisory_client import (
            observations_schema_hash,
        )

        # Physically scope the store under tenant/[project] (defense in depth on
        # top of the namespace+project already folded into the cache key).
        store_root = Path(settings.kimi_cache_dir) / cache_namespace
        if cache_project:
            store_root = store_root / cache_project
        ttl_seconds = (
            settings.kimi_cache_ttl_days * 86400.0 if settings.kimi_cache_ttl_days else None
        )
        reader = CachingVlmReader(
            client,
            FilesystemVlmResponseStore(store_root, ttl_seconds=ttl_seconds),
            model=settings.kimi_model,
            endpoint=settings.kimi_api_base_url or "",
            request_schema_hash=observations_schema_hash(),
            reasoning_effort=settings.kimi_reasoning_effort,
            cache_namespace=cache_namespace,
            cache_project=cache_project or "",
        )
    return RegionRestrictedVlmPipeline(
        region_detector=current.resolve(Tokens.DRAWING_REGION_DETECTOR),
        reader=reader,  # type: ignore[arg-type]
        cropper=_build_region_cropper(current),
        ready=True,
    )


def _build_extraction_integrity_producer(current: Container):
    backend = resolve_pdf_backend(current.resolve(Tokens.SETTINGS).pdf_backend)
    if backend == "none":
        return DisabledPdfExtractionIntegrityProducer()
    if backend == "pymupdf":
        return PyMuPDFExtractionIntegrityProducer()
    # Default: text-layer (pdfminer) + optional OCR when RapidOCR is installed.
    return OcrAwareExtractionIntegrityProducer()


def _build_region_cropper(current: Container):
    backend = resolve_pdf_backend(current.resolve(Tokens.SETTINGS).pdf_backend)
    if backend == "pymupdf":
        return PyMuPDFRegionCropper()
    return PdfiumRegionCropper()


def _build_audit_report_store(current: Container):
    settings = current.resolve(Tokens.SETTINGS)
    object_store = current.resolve(Tokens.OBJECT_STORE)
    payload_store = FilesystemAuditStore(
        settings.storage_dir,
        object_store=object_store,
        report_ttl_days=settings.report_ttl_days,
        fail_closed=settings.audit_fail_closed,
    )
    if settings.db_url:
        try:
            return PostgresAuditStore(db_url=settings.db_url, payload_store=payload_store)
        except Exception:
            # Fail-closed when audit_fail_closed / hard profile — no silent FS fallback.
            if settings.audit_fail_closed or not settings.is_dev_environment:
                raise
            return payload_store
    return payload_store
