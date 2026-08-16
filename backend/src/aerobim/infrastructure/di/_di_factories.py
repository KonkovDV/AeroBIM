from __future__ import annotations

import json
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.path_jail import resolve_storage_path
from aerobim.domain.hybrid.model_router import ModelRouter, ProviderRegistry
from aerobim.domain.llm_advisory import LlmProvider
from aerobim.domain.pdf_backend import resolve_pdf_backend
from aerobim.domain.ports import (
    AnalyzeProjectPackageJobStore,
    AuditReportStore,
    BcfApiClient,
    BsiValidationService,
    ExtractionIntegritySignalProducer,
    ObjectStore,
)
from aerobim.infrastructure.adapters.bsi_validation_service import (
    HttpBsiValidationService,
    LocalSchemaPackCertificate,
)
from aerobim.infrastructure.adapters.disabled_pdf_extraction_integrity_producer import (
    DisabledPdfExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.http_bcf_api_client import HttpBcfApiClient
from aerobim.infrastructure.adapters.hybrid_drawing_analyzer import HybridDrawingAnalyzer
from aerobim.infrastructure.adapters.ifc_system_aware_clash import IfcSystemAwareClash
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.llm_extraction_adapters import (
    OpenAICompatLlmExtractionAdapter,
)
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.adapters.multimodal_drawing_analyzer_port import (
    MultimodalDrawingAnalyzerPort,
)
from aerobim.infrastructure.adapters.ocr_aware_extraction_integrity_producer import (
    OcrAwareExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.pdfium_region_cropper import PdfiumRegionCropper
from aerobim.infrastructure.adapters.postgres_audit_store import PostgresAuditStore
from aerobim.infrastructure.adapters.pymupdf_extraction_integrity_producer import (
    PyMuPDFExtractionIntegrityProducer,
)
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import (
    RedisAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)
from aerobim.infrastructure.adapters.s3_object_store import S3ObjectStore
from aerobim.infrastructure.adapters.unconfigured_bcf_api_client import UnconfiguredBcfApiClient
from aerobim.infrastructure.adapters.unconfigured_system_clash import UnconfiguredSystemClash
from aerobim.infrastructure.security.oidc_token_validator import OidcTokenValidator


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


def _build_object_store(settings: Settings) -> ObjectStore:
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


def _build_job_store(settings: Settings) -> AnalyzeProjectPackageJobStore:
    if not settings.is_dev_environment:
        if not settings.redis_url:
            raise RuntimeError(
                "AEROBIM_REDIS_URL is required outside development/test; "
                "in-memory analyze job store is not allowed"
            )
        return RedisAnalyzeProjectPackageJobStore(settings.redis_url)
    if settings.redis_url:
        try:
            return RedisAnalyzeProjectPackageJobStore(settings.redis_url)
        except RuntimeError:
            pass
    return InMemoryAnalyzeProjectPackageJobStore(
        snapshot_path=settings.storage_dir / "analyze_project_package_jobs.snapshot.json"
    )


def _build_bcf_api_client(settings: Settings) -> BcfApiClient:
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
            raise ValueError("provider config must be an object with profiles")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"AEROBIM_HYBRID_PROVIDER_CONFIG invalid: {path}: {exc}") from exc
    return ModelRouter(ProviderRegistry.from_config(data))


def _build_llm_extraction_adapter(
    settings: Settings, *, provider_label: str
) -> OpenAICompatLlmExtractionAdapter:
    """Advisory extraction adapter; skipped/offline when label not the active provider."""

    label = provider_label.strip().lower()
    configured = settings.llm_provider.strip().lower()
    live = bool(
        settings.llm_local_ready()
        and (
            configured == label
            or configured.endswith(f"_{label}")
            or configured.endswith(f"_{label}_local")
            or label in configured.split("-")
            or label in configured.split("_")
        )
    )
    return OpenAICompatLlmExtractionAdapter(
        provider=label,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        allowed_hosts=frozenset(settings.llm_allowed_hosts),
        live=live,
    )


def _build_llm_advisory_provider(settings: Settings) -> LlmProvider:
    """OpenAI-compat advisory provider (vLLM / Yandex AI Studio) or disabled stub."""

    from aerobim.domain.llm_advisory import DisabledLlmProvider
    from aerobim.domain.llm_token_budget import LlmTokenBudget
    from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider

    if not settings.llm_local_ready():
        return DisabledLlmProvider()
    if settings.llm_budget_ledger_path is None:
        # RT-031: never arm Studio/local LLM with process-local day counters only.
        raise RuntimeError(
            "AEROBIM_LLM_BUDGET_LEDGER is required when LLM advisory is ready "
            "(RT-031 fail-closed shared day cap)"
        )
    from aerobim.infrastructure.adapters.file_llm_token_budget import FileBackedLlmTokenBudget

    budget_kwargs = {
        "max_tokens_per_call": settings.llm_max_tokens_per_call,
        "max_tokens_per_run": settings.llm_max_tokens_per_run,
        "max_tokens_per_day": settings.llm_max_tokens_per_day,
        "budget_tz": settings.llm_budget_tz,
    }
    budget: LlmTokenBudget = FileBackedLlmTokenBudget(
        settings.llm_budget_ledger_path,
        **budget_kwargs,
    )
    extra_headers: dict[str, str] = {}
    if settings.llm_folder_id:
        extra_headers["x-folder-id"] = settings.llm_folder_id
    # Always emit explicit logging preference for Studio / RF endpoints.
    if settings.llm_provider.strip().lower() == "yandex-ai-studio" or settings.llm_folder_id:
        extra_headers["x-data-logging-enabled"] = (
            "true" if settings.llm_data_logging_enabled else "false"
        )
    return OpenAICompatLlmProvider(
        base_url=settings.llm_base_url or "",
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        provider=settings.llm_provider,
        model_sha256=settings.llm_model_sha256,
        model_revision=settings.llm_model_revision,
        folder_id=settings.llm_folder_id,
        timeout_seconds=settings.llm_timeout_seconds,
        budget=budget,
        max_completion_tokens=settings.llm_max_completion_tokens,
        allowed_hosts=frozenset(settings.llm_allowed_hosts),
        extra_headers=extra_headers,
        auth_scheme=settings.llm_auth_scheme,
        send_seed=settings.llm_send_seed,
        response_schema_mode=(
            "json_schema"
            if settings.llm_response_format_mode.strip().lower() == "json_schema"
            else "json_object"
        ),
        max_concurrent=settings.llm_max_concurrent,
        retries_429=settings.llm_429_retries,
    )


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


def _build_bsi_validation_service(settings: Settings) -> BsiValidationService | None:
    if settings.bsi_validation_url and settings.bsi_api_token:
        return HttpBsiValidationService(
            base_url=settings.bsi_validation_url,
            api_token=settings.bsi_api_token,
        )
    if settings.bsi_local_cert:
        return LocalSchemaPackCertificate()
    return None


def _build_system_clash(settings: Settings) -> IfcSystemAwareClash | UnconfiguredSystemClash:
    if settings.mep_system_clash_enabled:
        return IfcSystemAwareClash(
            enabled=True,
            scope_memo_ref=settings.mep_scope_memo_ref,
        )
    return UnconfiguredSystemClash()


def _build_drawing_analyzer_port(
    current: Container,
) -> HybridDrawingAnalyzer | MultimodalDrawingAnalyzerPort:
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

    Constructed ready only when ``settings.vlm_advisory_ready()`` (opt-in, and
    hard-disabled on samolet_pilot / production). Even when ready it is not wired
    into the deterministic use case, so toggling the flag cannot change
    ``summary.passed`` (advisory OFF==ON). A future advisory surface may consume
    it, but must keep candidate regions out of ``engine_issues``.
    """
    settings = current.resolve(Tokens.SETTINGS)
    if not settings.vlm_advisory_ready():
        return RegionRestrictedVlmPipeline(
            region_detector=None, reader=None, cropper=None, ready=False
        )
    from aerobim.infrastructure.adapters.vlm_advisory_client import VlmAdvisoryClient

    client = VlmAdvisoryClient(
        base_url=settings.vlm_api_base_url or "",
        api_key=settings.vlm_api_key or "",
        model=settings.vlm_model,
        reasoning_effort=settings.vlm_reasoning_effort,
        allowed_hosts=frozenset(settings.llm_allowed_hosts),
        # Yandex Studio (and similar) need auth scheme + folder from the LLM contour.
        auth_scheme=settings.llm_auth_scheme,
        folder_id=settings.llm_folder_id,
    )
    # §2.1/§5: deterministic act-grade replay ONLY with a trusted tenant scope.
    # The pipeline is a process singleton with no per-request identity, so a
    # persistent cache without a validated namespace could replay one tenant's
    # response for another. Fail closed: no namespace -> no persistent cache.
    reader: object = client
    cache_namespace = _safe_cache_namespace(settings.vlm_cache_namespace)
    # A configured-but-invalid project fails closed (None); unset project -> "".
    cache_project = (
        _safe_cache_namespace(settings.vlm_cache_project) if settings.vlm_cache_project else ""
    )
    if settings.vlm_cache_dir and cache_namespace and cache_project is not None:
        from aerobim.infrastructure.adapters.caching_vlm_reader import (
            CachingVlmReader,
            FilesystemVlmResponseStore,
        )
        from aerobim.infrastructure.adapters.vlm_advisory_client import (
            observations_schema_hash,
        )

        # Physically scope the store under tenant/[project] (defense in depth on
        # top of the namespace+project already folded into the cache key).
        store_root = Path(settings.vlm_cache_dir) / cache_namespace
        if cache_project:
            store_root = store_root / cache_project
        ttl_seconds = settings.vlm_cache_ttl_days * 86400.0 if settings.vlm_cache_ttl_days else None
        reader = CachingVlmReader(
            client,
            FilesystemVlmResponseStore(store_root, ttl_seconds=ttl_seconds),
            model=settings.vlm_model,
            endpoint=settings.vlm_api_base_url or "",
            request_schema_hash=observations_schema_hash(),
            reasoning_effort=settings.vlm_reasoning_effort,
            cache_namespace=cache_namespace,
            cache_project=cache_project or "",
        )
    return RegionRestrictedVlmPipeline(
        region_detector=current.resolve(Tokens.DRAWING_REGION_DETECTOR),
        reader=reader,  # type: ignore[arg-type]
        cropper=_build_region_cropper(current),
        ready=True,
    )


def _build_extraction_integrity_producer(current: Container) -> ExtractionIntegritySignalProducer:
    backend = resolve_pdf_backend(current.resolve(Tokens.SETTINGS).pdf_backend)
    if backend == "none":
        return DisabledPdfExtractionIntegrityProducer()
    if backend == "pymupdf":
        return PyMuPDFExtractionIntegrityProducer()
    # Default: text-layer (pdfminer) + optional OCR when RapidOCR is installed.
    return OcrAwareExtractionIntegrityProducer()


def _build_region_cropper(current: Container) -> PyMuPDFRegionCropper | PdfiumRegionCropper:
    # Heuristic detector + PII plan emit normalized-0-1; page-point default would
    # silently crop ~1pt boxes (RT-STAMP-09 / CRS mismatch).
    backend = resolve_pdf_backend(current.resolve(Tokens.SETTINGS).pdf_backend)
    if backend == "pymupdf":
        return PyMuPDFRegionCropper(coordinate_system="normalized-0-1")
    return PdfiumRegionCropper(coordinate_system="normalized-0-1")


def _build_audit_report_store(current: Container) -> AuditReportStore:
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
            return PostgresAuditStore(
                db_url=settings.db_url,
                payload_store=payload_store,
                apply_ddl=settings.postgres_apply_ddl,
            )
        except Exception:
            # Fail-closed when audit_fail_closed / hard profile — no silent FS fallback.
            if settings.audit_fail_closed or not settings.is_dev_environment:
                raise
            return payload_store
    return payload_store
