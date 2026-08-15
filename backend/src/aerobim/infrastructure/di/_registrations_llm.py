from __future__ import annotations

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.adapters.llm_extraction_adapters import (
    RegexRequirementExtractionAdapter,
)
from aerobim.infrastructure.di._di_factories import (
    _build_advisory_vlm_pipeline,
    _build_llm_advisory_provider,
    _build_llm_extraction_adapter,
    _build_model_router,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
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
    # Local OpenAI-compat LLM (Qwen via vLLM) — advisory remark compose only; not verdict.
    container.register(
        Tokens.LLM_ADVISORY_PROVIDER,
        lambda current: _build_llm_advisory_provider(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    # Experimental advisory extraction — NEVER consumed by AnalyzeProjectPackageUseCase.
    container.register(
        Tokens.LLM_EXTRACTION_REGEX,
        lambda _current: RegexRequirementExtractionAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.LLM_EXTRACTION_KIMI,
        lambda current: _build_llm_extraction_adapter(
            current.resolve(Tokens.SETTINGS), provider_label="kimi"
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.LLM_EXTRACTION_QWEN,
        lambda current: _build_llm_extraction_adapter(
            current.resolve(Tokens.SETTINGS), provider_label="qwen"
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
