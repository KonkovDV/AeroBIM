from __future__ import annotations

from aerobim.application.services.agentic_review_orchestrator import AgenticReviewOrchestrator
from aerobim.application.services.compliance_agent_orchestrator import ComplianceAgentOrchestrator
from aerobim.application.services.determinism_gate import DeterminismGate
from aerobim.application.use_cases.apply_norm_rule_hitl_event import ApplyNormRuleHitlEventUseCase
from aerobim.application.use_cases.compile_requirements_to_ids import (
    CompileRequirementsToIdsUseCase,
)
from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import Severity, ToleranceConfig
from aerobim.domain.ports import BsiValidationService
from aerobim.infrastructure.adapters.basic_ifc_schema_validator import BasicIfcSchemaValidator
from aerobim.infrastructure.adapters.deterministic_requirement_interpreter import (
    DeterministicRequirementInterpreter,
)
from aerobim.infrastructure.adapters.deterministic_requirement_to_ids_compiler import (
    DeterministicRequirementToIdsCompiler,
)
from aerobim.infrastructure.adapters.filesystem_norm_corpus_retriever import (
    FilesystemNormCorpusRetriever,
)
from aerobim.infrastructure.adapters.ifc_guid_attribute_diff import IfcGuidAttributeDiffAdapter
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader
from aerobim.infrastructure.adapters.json_section_diff_analyzer import JsonSectionDiffAnalyzer
from aerobim.infrastructure.adapters.manifest_logic_consistency_adapter import (
    ManifestLogicConsistencyAdapter,
)
from aerobim.infrastructure.adapters.object_store_norm_pack_version_store import (
    ObjectStoreNormRulePackVersionStore,
)
from aerobim.infrastructure.adapters.relational_ifc_knowledge_graph import (
    RelationalIfcKnowledgeGraph,
)
from aerobim.infrastructure.adapters.spreadsheet_load_evidence_adapter import (
    SpreadsheetLoadEvidenceAdapter,
)
from aerobim.infrastructure.adapters.xml_ids_document_auditor import XmlIdsDocumentAuditor
from aerobim.infrastructure.di._di_factories import (
    _build_bsi_validation_service,
    _default_norm_corpus_roots,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
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
        Tokens.IFC_MODEL_DIFF,
        lambda _container: IfcGuidAttributeDiffAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
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
        Tokens.DETERMINISM_GATE,
        lambda _container: DeterminismGate(),
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
        Tokens.IFC_KNOWLEDGE_GRAPH,
        lambda _container: RelationalIfcKnowledgeGraph(),
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
    bsi_service = _build_bsi_validation_service(runtime_settings)
    if bsi_service is not None:
        registered_bsi = bsi_service

        def _resolve_bsi(_container: Container) -> BsiValidationService:
            return registered_bsi

        container.register(
            Tokens.BSI_VALIDATION_SERVICE,
            _resolve_bsi,
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
