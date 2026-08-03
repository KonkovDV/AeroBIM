"""OpenAI-compatible LLM provider (vLLM / Yandex AI Studio) for advisory text.

Supports ``private_qwen_local`` (loopback) and ``private_yandex_ai_studio`` (RF T2)
via the same class — ``base_url``, caps, response_format, seed, and vendor headers
change. Hard token budget fail-closed before any network call. Never sets
``summary.passed``. Alibaba Max out of scope.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any, Literal
from urllib.parse import urlparse

from aerobim.core.config.settings import (
    _DEFAULT_LLM_ALLOWED_HOSTS,
    assert_llm_base_host_allowed,
    resolve_llm_model_uri,
)
from aerobim.domain.advisory_remark_compose import REMARK_JSON_SCHEMA
from aerobim.domain.llm_advisory import LlmRequest, LlmResponse
from aerobim.domain.llm_token_budget import LlmTokenBudget

Transport = Callable[[str, dict[str, str], bytes], bytes]
ResponseSchemaMode = Literal["json_schema", "json_object"]

_DEFAULT_TIMEOUT = 60.0
_MAX_RESPONSE_BYTES = 1 * 1024 * 1024
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})


class OpenAICompatLlmProvider:
    """OpenAI ``/chat/completions`` client implementing ``LlmProvider``."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        provider: str = "qwen-local",
        model_sha256: str | None = None,
        model_revision: str | None = None,
        folder_id: str | None = None,
        temperature: float = 0.0,
        seed: int | None = 0,
        send_seed: bool = True,
        timeout_seconds: float = _DEFAULT_TIMEOUT,
        transport: Transport | None = None,
        budget: LlmTokenBudget | None = None,
        max_completion_tokens: int = 512,
        allowed_hosts: frozenset[str] | tuple[str, ...] | None = None,
        extra_headers: Mapping[str, str] | None = None,
        auth_scheme: str = "Bearer",
        response_schema_mode: ResponseSchemaMode = "json_object",
        max_concurrent: int = 4,
        retries_429: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = resolve_llm_model_uri(
            model=model,
            revision=model_revision,
            folder_id=folder_id,
        )
        self._model_revision = (model_revision or "").strip() or None
        self._folder_id = (folder_id or "").strip() or None
        self._api_key = api_key
        self._provider = provider
        self._model_sha256 = model_sha256
        self._temperature = temperature
        self._seed = seed
        self._send_seed = bool(send_seed)
        self._timeout = timeout_seconds
        self._transport = transport or self._default_transport
        self._budget = budget or LlmTokenBudget()
        self._max_completion_tokens = max(1, int(max_completion_tokens))
        self._allowed_hosts = frozenset(allowed_hosts or _DEFAULT_LLM_ALLOWED_HOSTS)
        self._extra_headers = {str(k): str(v) for k, v in dict(extra_headers or {}).items()}
        scheme = (auth_scheme or "Bearer").strip() or "Bearer"
        self._auth_scheme = scheme
        mode = (response_schema_mode or "json_object").strip().lower()
        if mode not in {"json_schema", "json_object"}:
            raise ValueError(f"unsupported response_schema_mode: {response_schema_mode!r}")
        self._response_schema_mode: ResponseSchemaMode = mode  # type: ignore[assignment]
        self._semaphore = threading.BoundedSemaphore(max(1, int(max_concurrent)))
        self._retries_429 = max(0, int(retries_429))
        # Defense-in-depth: re-check even if Settings was built without from_env.
        if self._base_url:
            assert_llm_base_host_allowed(self._base_url, self._allowed_hosts)

    def __repr__(self) -> str:
        host = urlparse(self._base_url).hostname or "unknown"
        return (
            f"OpenAICompatLlmProvider(provider={self._provider!r}, model={self._model!r}, "
            f"host={host!r}, model_sha256={(self._model_sha256 or '')[:12]!r})"
        )

    def _response_format(self) -> dict[str, Any]:
        if self._response_schema_mode == "json_schema":
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "advisory_remark",
                    "schema": REMARK_JSON_SCHEMA,
                },
            }
        return {"type": "json_object"}

    def _request_headers(self, *, client_request_id: str | None = None) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._extra_headers,
        }
        if client_request_id:
            # Yandex support correlation (DOC); primary audit is still AeroBIM audit_event.
            headers["x-client-request-id"] = client_request_id
        if self._api_key:
            headers["Authorization"] = f"{self._auth_scheme} {self._api_key}"
        return headers

    def _vendor_audit_fields(self) -> dict[str, Any]:
        """Non-secret vendor evidence for usage / audit_event (IB Samolet)."""

        logging_hdr = self._extra_headers.get("x-data-logging-enabled")
        return {
            "model_uri": self._model,
            "model_revision": self._model_revision,
            "response_format_mode": self._response_schema_mode,
            "seed_sent": bool(self._send_seed and self._seed is not None),
            "auth_scheme": self._auth_scheme,
            "folder_id_set": bool(self._folder_id or self._extra_headers.get("x-folder-id")),
            "data_logging_header": logging_hdr,
            "data_logging_disabled": str(logging_hdr).lower() == "false",
            "deterministic_intrasession": None,
            "stable_across_time": None,
            "reproducible": False,
        }

    def _call_transport(self, url: str, headers: dict[str, str], body: bytes) -> bytes:
        """Semaphore + 429 retry (D-1); cloud quota is shared across the org."""

        attempts = self._retries_429 + 1
        last_exc: BaseException | None = None
        with self._semaphore:
            for attempt in range(attempts):
                try:
                    return self._transport(url, headers, body)
                except urllib.error.HTTPError as exc:
                    last_exc = exc
                    if exc.code == 429 and attempt + 1 < attempts:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    raise
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    raise
        assert last_exc is not None
        raise last_exc

    def _default_transport(self, url: str, headers: dict[str, str], body: bytes) -> bytes:
        from aerobim.core.security.outbound_url import (
            safe_datastore_urlopen,
            safe_urlopen,
        )

        # Host allowlist again at call time (deny markers beat AEROBIM_LLM_ALLOWED_HOSTS).
        assert_llm_base_host_allowed(url, self._allowed_hosts)
        host = (urlparse(url).hostname or "").lower()
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        if host in _LOOPBACK:
            # Local vLLM: public SSRF guard rejects loopback — datastore seam.
            with safe_datastore_urlopen(request, timeout=self._timeout) as response:
                return response.read(_MAX_RESPONSE_BYTES + 1)
        # Yandex AI Studio / remote private endpoint — DNS-pinned SSRF guard.
        with safe_urlopen(request, timeout=self._timeout) as response:
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
                usage={**self._budget.snapshot(), **self._vendor_audit_fields()},
                status="blocked_by_policy",
                schema_valid=True,
                unsupported_claims=(),
            )

        # Estimate overshoots for Cyrillic (grant fail-closed): chars/2 not chars/3.
        estimate = (
            len(json.dumps(request.deterministic_findings, ensure_ascii=False)) // 2
            + 400
            + self._max_completion_tokens
        )
        blocked = self._budget.check_before(estimated_tokens=estimate)
        if blocked:
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=(blocked,),
                model=self._model,
                provider=self._provider,
                usage={**self._budget.snapshot(), **self._vendor_audit_fields()},
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
            "max_tokens": self._max_completion_tokens,
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
            "response_format": self._response_format(),
        }
        if self._seed is not None and self._send_seed:
            body_obj["seed"] = self._seed
        raw_body = json.dumps(body_obj, ensure_ascii=False).encode("utf-8")
        prompt_sha256 = hashlib.sha256(raw_body).hexdigest()
        headers = self._request_headers(client_request_id=request.request_id)
        audit_extra = {
            "prompt_sha256": prompt_sha256,
            "client_request_id": request.request_id,
        }

        try:
            raw = self._call_transport(
                f"{self._base_url}/chat/completions",
                headers,
                raw_body,
            )
        except Exception as exc:  # noqa: BLE001 — advisory fail-closed
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=(f"transport_error:{type(exc).__name__}",),
                model=self._model,
                provider=self._provider,
                usage={
                    **self._budget.snapshot(),
                    **self._vendor_audit_fields(),
                    **audit_extra,
                    **({"model_sha256": self._model_sha256} if self._model_sha256 else {}),
                },
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
                usage={**self._budget.snapshot(), **self._vendor_audit_fields()},
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
            raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        except (KeyError, IndexError, TypeError, ValueError, UnicodeDecodeError):
            return LlmResponse(
                remark_draft="",
                severity_suggestion=None,
                evidence_refs=request.evidence_refs,
                confidence=None,
                uncertainties=("schema_deviation",),
                model=self._model,
                provider=self._provider,
                usage={**self._budget.snapshot(), **self._vendor_audit_fields()},
                status="failed",
                schema_valid=False,
                unsupported_claims=(),
            )

        prompt_tokens = int(raw_usage.get("prompt_tokens") or 0)
        completion_tokens = int(raw_usage.get("completion_tokens") or 0)
        if prompt_tokens == 0 and completion_tokens == 0:
            # Provider omitted usage — charge the pre-call estimate (fail-closed for grant).
            prompt_tokens = max(0, estimate - self._max_completion_tokens)
            completion_tokens = self._max_completion_tokens
        usage = self._budget.record(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        response_sha256 = hashlib.sha256(draft.encode("utf-8")).hexdigest()
        usage = {
            **usage,
            **self._vendor_audit_fields(),
            **audit_extra,
            "response_sha256": response_sha256,
        }
        if self._model_sha256:
            usage = {**usage, "model_sha256": self._model_sha256}

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
