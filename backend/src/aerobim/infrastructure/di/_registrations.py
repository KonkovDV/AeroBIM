from __future__ import annotations

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.di._di_factories import (
    _resolve_default_norm_pack_path,
    _resolve_mep_federated_scope_path,
)
from aerobim.infrastructure.di._registrations_audit import register_group as register_audit
from aerobim.infrastructure.di._registrations_auth import register_group as register_auth
from aerobim.infrastructure.di._registrations_bcf import register_group as register_bcf
from aerobim.infrastructure.di._registrations_clash import register_group as register_clash
from aerobim.infrastructure.di._registrations_compliance import (
    register_group as register_compliance,
)
from aerobim.infrastructure.di._registrations_ingestion import (
    register_group as register_ingestion,
)
from aerobim.infrastructure.di._registrations_llm import register_group as register_llm
from aerobim.infrastructure.di._registrations_storage import register_group as register_storage


def register_all(container: Container, runtime_settings: Settings) -> None:
    tolerance = ToleranceConfig()
    container.register(Tokens.SETTINGS, lambda _container: runtime_settings)
    register_ingestion(container, runtime_settings, tolerance=tolerance)
    register_clash(container, runtime_settings, tolerance=tolerance)
    register_llm(container, runtime_settings, tolerance=tolerance)
    register_audit(container, runtime_settings, tolerance=tolerance)
    register_bcf(container, runtime_settings, tolerance=tolerance)
    register_auth(container, runtime_settings, tolerance=tolerance)
    register_compliance(container, runtime_settings, tolerance=tolerance)
    register_storage(container, runtime_settings, tolerance=tolerance)
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
            llm_advisory_provider=current.resolve(Tokens.LLM_ADVISORY_PROVIDER),
            remark_locale=current.resolve(Tokens.SETTINGS).remark_locale,
            llm_advisory_max_issues=current.resolve(Tokens.SETTINGS).llm_advisory_max_issues,
            llm_max_concurrent=current.resolve(Tokens.SETTINGS).llm_max_concurrent,
            space_efficiency_advisory_enabled=True,
            space_inventory_extractor=current.resolve(Tokens.IFC_SPACE_INVENTORY),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
