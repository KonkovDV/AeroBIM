"""OpenAI-compatible local LLM provider (vLLM / SGLang) for advisory text.

Designed for ``private_qwen_local``: temperature=0, JSON object, injectable
transport (CI never hits the network). Never sets ``summary.passed``.
Cloud Max / public Model Studio is out of scope for this adapter.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from aerobim.domain.advisory_remark_compose import REMARK_JSON_SCHEMA
from aerobim.domain.llm_advisory import LlmRequest, LlmResponse

Transport = Callable[[str, dict[str, str], bytes], bytes]

_DEFAULT_TIMEOUT = 60.0
_MAX_RESPONSE_BYTES = 1 * 1024 * 1024


class OpenAICompatLlmProvider:
    """Local OpenAI ``/chat/completions`` client implementing ``LlmProvider``."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        provider: str = "qwen-local",
        model_sha256: str | None = None,
        temperature: float = 0.0,
        seed: int | None = 0,
        timeout_seconds: float = _DEFAULT_TIMEOUT,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._provider = provider
        self._model_sha256 = model_sha256
        self._temperature = temperature
        self._seed = seed
        self._timeout = timeout_seconds
        self._transport = transport or self._default_transport

    def __repr__(self) -> str:
        host = urlparse(self._base_url).hostname or "unknown"
        return (
            f"OpenAICompatLlmProvider(provider={self._provider!r}, model={self._model!r}, "
            f"host={host!r}, model_sha256={(self._model_sha256 or '')[:12]!r})"
        )

    def _default_transport(self, url: str, headers: dict[str, str], body: bytes) -> bytes:
        from aerobim.core.security.outbound_url import assert_safe_datastore_url

        # Local vLLM is loopback; public SSRF guard rejects localhost — use datastore gate.
        assert_safe_datastore_url(url, resolve_dns=False)
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return response.read(_MAX_RESPONSE_BYTES + 1)

    def generate(self, request: LlmRequest) -> LlmResponse:
        deny_all = (
            not request.data_policy.allow_synthetic_public
            and not request.data_policy.allow_customer_data
        )
        if deny_all:
            return LlmResponse(
                remark_draft="",
                severity_suggestion="review_required",
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

        user_payload = {
            "request_id": request.request_id,
            "allowed_task": request.allowed_task,
            "forbidden_actions": list(request.forbidden_actions),
            "requirements": list(request.requirements),
            "deterministic_findings": list(request.deterministic_findings),
            "evidence_refs": list(request.evidence_refs),
            "response_schema": REMARK_JSON_SCHEMA,
        }
        body_obj: dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an advisory engineering remark composer. "
                        "Output JSON only. Never invent findings. Never set a verdict."
                    ),
                },
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        if self._seed is not None:
            body_obj["seed"] = self._seed
        raw_body = json.dumps(body_obj, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            raw = self._transport(f"{self._base_url}/chat/completions", headers, raw_body)
        except Exception as exc:  # noqa: BLE001 — advisory fail-closed
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=(f"transport_error:{type(exc).__name__}",),
                model=self._model,
                provider=self._provider,
                usage={"model_sha256": self._model_sha256} if self._model_sha256 else {},
                status="failed",
                schema_valid=False,
                unsupported_claims=(),
            )

        if len(raw) > _MAX_RESPONSE_BYTES:
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=("truncated",),
                model=self._model,
                provider=self._provider,
                usage={},
                status="failed",
                schema_valid=False,
                unsupported_claims=(),
            )

        try:
            payload = json.loads(raw.decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            draft = str(content or "").strip()
            usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        except (KeyError, IndexError, TypeError, ValueError, UnicodeDecodeError):
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=("schema_deviation",),
                model=self._model,
                provider=self._provider,
                usage={},
                status="failed",
                schema_valid=False,
                unsupported_claims=(),
            )

        schema_valid = False
        if draft.startswith("{"):
            try:
                parsed = json.loads(draft)
                schema_valid = (
                    isinstance(parsed, dict)
                    and isinstance(parsed.get("title"), str)
                    and isinstance(parsed.get("body"), str)
                    and isinstance(parsed.get("locale"), str)
                    and isinstance(parsed.get("evidence_refs"), list)
                )
            except json.JSONDecodeError:
                schema_valid = False

        if self._model_sha256:
            usage = {**usage, "model_sha256": self._model_sha256}

        return LlmResponse(
            remark_draft=draft if schema_valid else "",
            severity_suggestion="warning",
            evidence_refs=request.evidence_refs,
            confidence=None,
            uncertainties=() if schema_valid else ("schema_deviation",),
            model=self._model,
            provider=self._provider,
            usage=usage,
            status="advisory" if schema_valid else "failed",
            schema_valid=schema_valid,
            unsupported_claims=(),
        )


__all__ = ["OpenAICompatLlmProvider"]
