"""DI container entry point — delegates registration to grouped modules."""

from __future__ import annotations

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.infrastructure.di._di_factories import (
    _build_advisory_vlm_pipeline,
    _build_audit_report_store,
    _build_bcf_api_client,
    _build_bsi_validation_service,
    _build_drawing_analyzer_port,
    _build_extraction_integrity_producer,
    _build_job_store,
    _build_llm_advisory_provider,
    _build_llm_extraction_adapter,
    _build_model_router,
    _build_object_store,
    _build_oidc_validator,
    _build_system_clash,
    _default_norm_corpus_roots,
    _resolve_default_norm_pack_path,
    _resolve_mep_federated_scope_path,
    _safe_cache_namespace,
)
from aerobim.infrastructure.di._registrations import register_all

__all__ = [
    "bootstrap_container",
    "_build_advisory_vlm_pipeline",
    "_build_audit_report_store",
    "_build_bcf_api_client",
    "_build_bsi_validation_service",
    "_build_drawing_analyzer_port",
    "_build_extraction_integrity_producer",
    "_build_job_store",
    "_build_llm_advisory_provider",
    "_build_llm_extraction_adapter",
    "_build_model_router",
    "_build_object_store",
    "_build_oidc_validator",
    "_build_system_clash",
    "_default_norm_corpus_roots",
    "_resolve_default_norm_pack_path",
    "_resolve_mep_federated_scope_path",
    "_safe_cache_namespace",
]


def bootstrap_container(settings: Settings | None = None) -> Container:
    container = Container()
    runtime_settings = settings or Settings.from_env()
    runtime_settings.require_secure_auth()
    runtime_settings.storage_dir.mkdir(parents=True, exist_ok=True)

    from aerobim.infrastructure.adapters.ifc_file_open import configure_ifc_parse_cache

    configure_ifc_parse_cache(runtime_settings.ifc_parse_cache_dir)
    register_all(container, runtime_settings)
    return container
