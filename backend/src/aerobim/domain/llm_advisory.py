"""Advisory LLM provider contract (verdict-neutral; no secrets in domain)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

LlmAdvisoryStatus = Literal[
    "disabled",
    "configured",
    "available",
    "failed",
    "blocked_by_policy",
    "not_verified",
]

FORBIDDEN_LLM_ACTIONS = frozenset(
    {
        "change_verdict",
        "approve_norm",
        "call_tool",
        "send_data",
        "modify_source",
    }
)


@dataclass(frozen=True)
class LlmDataPolicy:
    """Egress / retention policy for advisory LLM calls."""

    allow_customer_data: bool = False
    allow_synthetic_public: bool = False
    training_use_forbidden: bool = True
    retention_unknown: bool = True
    profile: str = "default_deny_customer"


@dataclass(frozen=True)
class LlmRequest:
    request_id: str
    source_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    deterministic_findings: tuple[dict[str, Any], ...] = ()
    requirements: tuple[str, ...] = ()
    allowed_task: str = "compose_or_rank_advisory_remark"
    forbidden_actions: tuple[str, ...] = tuple(sorted(FORBIDDEN_LLM_ACTIONS))
    data_policy: LlmDataPolicy = field(default_factory=LlmDataPolicy)


@dataclass(frozen=True)
class LlmResponse:
    remark_draft: str
    severity_suggestion: str | None
    evidence_refs: tuple[str, ...]
    confidence: float | None
    uncertainties: tuple[str, ...]
    model: str
    provider: str
    usage: dict[str, Any]
    status: str = "advisory"
    schema_valid: bool = True
    unsupported_claims: tuple[str, ...] = ()


@dataclass(frozen=True)
class LlmAuditRecord:
    request_id: str
    provider: str
    model: str
    latency_ms: float
    status: str
    error_class: str | None = None
    token_usage: dict[str, Any] = field(default_factory=dict)
    # Never include API keys, full prompts with confidential docs, or secrets.


@dataclass(frozen=True)
class LLMRunManifest:
    request_id: str
    provider: str
    model: str
    base_url_host: str | None
    data_policy: LlmDataPolicy
    advisory_only: bool = True
    affects_summary_passed: bool = False


@dataclass(frozen=True)
class LlmEvidenceContract:
    """Advisory outputs must stay bounded to supplied evidence refs."""

    require_evidence_refs: bool = True
    allow_invented_findings: bool = False
    allow_verdict_mutation: bool = False


@dataclass(frozen=True)
class LlmProviderCapabilities:
    provider: str
    models: tuple[str, ...]
    supports_streaming: bool = False
    data_policy_status: str = "CLOUD_DATA_POLICY_UNKNOWN"
    customer_data_allowed: bool = False


class LlmProvider(Protocol):
    """Infrastructure adapters implement this; domain stays SDK-free."""

    def generate(self, request: LlmRequest) -> LlmResponse: ...


class MockLlmProvider:
    """Deterministic mock for Kimi/Qwen/Gemma contract tests (no network)."""

    def __init__(self, *, provider: str, model: str) -> None:
        self._provider = provider
        self._model = model

    def generate(self, request: LlmRequest) -> LlmResponse:
        deny_all = (
            not request.data_policy.allow_synthetic_public
            and not request.data_policy.allow_customer_data
        )
        if deny_all:
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=(),
                confidence=None,
                uncertainties=("blocked_by_policy",),
                model=self._model,
                provider=self._provider,
                usage={},
                status="blocked_by_policy",
                schema_valid=True,
                unsupported_claims=(),
            )
        refs = request.evidence_refs or ("deterministic",)
        # Refuse unsupported product claims if requirements mention them.
        forbidden_phrases = (
            "точность >90%",
            "замена эксперта",
            "DWG-ready",
            "CDE interoperable",
        )
        unsupported = tuple(
            phrase
            for phrase in forbidden_phrases
            if any(phrase in item for item in request.requirements)
        )
        draft = "Advisory remark grounded in deterministic findings only. Expert review required."
        if unsupported:
            draft = "Refused: unsupported product claim in prompt context."
        return LlmResponse(
            remark_draft=draft,
            severity_suggestion=None,
            evidence_refs=tuple(refs),
            confidence=None,
            uncertainties=("verbalized_confidence_uncalibrated",),
            model=self._model,
            provider=self._provider,
            usage={"prompt_tokens": 0, "completion_tokens": 0},
            status="advisory",
            schema_valid=True,
            unsupported_claims=unsupported,
        )


class DisabledLlmProvider:
    """Fail-closed placeholder when local LLM is not configured (SKIPPED, not FAILED)."""

    def generate(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(
            remark_draft="",
            severity_suggestion=None,
            evidence_refs=request.evidence_refs,
            confidence=None,
            uncertainties=("llm_local_disabled",),
            model="none",
            provider="disabled",
            usage={},
            status="disabled",
            schema_valid=True,
            unsupported_claims=(),
        )


def llm_advisory_capability_status(
    *,
    configured: bool,
    policy_blocks: bool,
    available: bool,
) -> LlmAdvisoryStatus:
    if policy_blocks:
        return "blocked_by_policy"
    if not configured:
        return "disabled"
    if available:
        return "available"
    return "not_verified"


__all__ = [
    "DisabledLlmProvider",
    "FORBIDDEN_LLM_ACTIONS",
    "LLMRunManifest",
    "LlmAdvisoryStatus",
    "LlmAuditRecord",
    "LlmDataPolicy",
    "LlmEvidenceContract",
    "LlmProvider",
    "LlmProviderCapabilities",
    "LlmRequest",
    "LlmResponse",
    "MockLlmProvider",
    "llm_advisory_capability_status",
]
