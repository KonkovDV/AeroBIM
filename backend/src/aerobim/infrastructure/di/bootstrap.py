from __future__ import annotations

from pathlib import Path

from aerobim.application.services.agentic_review_orchestrator import AgenticReviewOrchestrator
from aerobim.application.services.compliance_agent_orchestrator import ComplianceAgentOrchestrator
from aerobim.application.services.determinism_gate import DeterminismGate
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
from aerobim.domain.models import Severity, ToleranceConfig
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
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
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
from aerobim.infrastructure.adapters.ocr_fallback_multimodal_drawing_pipeline import (
    OcrFallbackMultimodalDrawingPipeline,
)
from aerobim.infrastructure.adapters.oda_cad_model_ingestor import OdaCadModelIngestor
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import OpenRebarEvidenceVerifier
from aerobim.infrastructure.adapters.postgres_audit_store import PostgresAuditStore
from aerobim.infrastructure.adapters.raster_drawing_analyzer import RasterDrawingAnalyzer
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import (
    RedisAnalyzeProjectPackageJobStore,
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


def _build_oidc_validator(settings: Settings) -> OidcTokenValidator | None:
    if not settings.oidc_enabled:
        return None
    assert settings.oidc_issuer and settings.oidc_audience and settings.oidc_jwks_url
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
