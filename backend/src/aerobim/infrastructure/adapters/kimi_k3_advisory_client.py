"""VLM advisory client — OpenAI-compatible, SSRF-guarded, per-model profile.

Advisory only (ADR-001 / TR-31): returns a raw structured response for
``vlm_grounding`` to turn into **candidate** regions. It never decides a verdict.

Model contract (verified vs platform.kimi.ai, Jul 2026) is per-profile, because
the pilot target is a small Kimi-VL served by **vLLM** (tier C), not the
2.8T ``kimi-k3`` API (tier A):

- ``kimi-k3`` API fixes sampling ("cannot be modified") → we do NOT send
  ``temperature`` (sending it would be misleading); reproducibility for the
  МИК act comes from snapshot pin + full request/response logging + golden-hash
  replay, recorded as ``determinism_basis="sampling_fixed_by_service"``. It also
  supports strict ``json_schema`` and top-level ``reasoning_effort``, and may run
  a billable built-in web-search → we disable server tools explicitly.
- self-hosted vLLM VLM honours ``temperature=0`` (``determinism_basis=
  "temperature_zero"``), typically speaks ``json_object`` (guided-json varies by
  version), has no ``reasoning_effort`` and no built-in tools.

Security: outbound via the shared SSRF guard (DNS-pinned, no redirects,
private/metadata blocked); response body byte-capped; API key only in the
Authorization header, redacted from ``repr``.

The ``transport`` seam is injectable so tests never touch the network.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

_DEFAULT_TIMEOUT_SECONDS = 60.0
_DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024

# transport(url, headers, body) -> response bytes
Transport = Callable[[str, dict[str, str], bytes], bytes]

ReasonCode = Literal["TRANSPORT_ERROR", "SCHEMA_DEVIATION", "TRUNCATED", "EMPTY_CONTENT"]

# Strict schema for the current regions contract (the richer §4 observation
# schema with our-side normalized_value is a sequenced follow-up).
_DRAWING_REGIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "coordinate_system": {"type": "string"},
        "regions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "text": {"type": "string"},
                    "field": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["bbox", "confidence"],
            },
        },
    },
    "required": ["regions"],
}

# §4 rich region-observation schema (strict). normalized_value is echoed by the
# model but IGNORED by grounding — we recompute it deterministically.
_OBSERVATIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sheet_id": {"type": "string"},
        "region_id": {"type": "string"},
        "readable": {"type": "boolean"},
        "unreadable_reason": {"type": ["string", "null"]},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "text",
                            "dimension",
                            "designation",
                            "table_row",
                            "stamp_field",
                        ],
                    },
                    "raw_value": {"type": "string"},
                    "normalized_value": {"type": ["string", "null"]},
                    "bbox_rel": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "confidence": {"type": "number"},
                    "evidence_note": {"type": "string"},
                },
                "required": ["kind", "raw_value", "bbox_rel", "confidence"],
            },
        },
    },
    "required": ["readable", "observations"],
}


def observations_schema_hash() -> str:
    """Stable hash of the §4 observations schema (recorded in cache provenance)."""
    from aerobim.domain.vlm_cache import content_sha256

    return content_sha256(_OBSERVATIONS_SCHEMA)


@dataclass(frozen=True)
class KimiModelProfile:
    """Per-model request-shaping capabilities (avoids breaking the tier-C vLLM path)."""

    model_id: str
    send_temperature: bool
    response_format: dict[str, Any]
    supports_reasoning_effort: bool
    disable_server_tools: bool
    determinism_basis: str  # sampling_fixed_by_service | temperature_zero


def _strict_regions_response_format() -> dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "aerobim_drawing_read",
            "strict": True,
            "schema": _DRAWING_REGIONS_SCHEMA,
        },
    }


def kimi_k3_api_profile(model_id: str = "kimi-k3") -> KimiModelProfile:
    return KimiModelProfile(
        model_id=model_id,
        send_temperature=False,
        response_format=_strict_regions_response_format(),
        supports_reasoning_effort=True,
        disable_server_tools=True,
        determinism_basis="sampling_fixed_by_service",
    )


def vllm_vlm_profile(model_id: str) -> KimiModelProfile:
    return KimiModelProfile(
        model_id=model_id,
        send_temperature=True,
        response_format={"type": "json_object"},
        supports_reasoning_effort=False,
        disable_server_tools=False,
        determinism_basis="temperature_zero",
    )


def profile_for(model_id: str) -> KimiModelProfile:
    """Default profile inference; anything not the kimi-k3 API is treated as vLLM."""
    return (
        kimi_k3_api_profile(model_id)
        if model_id.strip().lower().startswith("kimi-k3")
        else vllm_vlm_profile(model_id)
    )


@dataclass(frozen=True)
class KimiReadResult:
    """Client output: structured content + billing usage + determinism basis."""

    content: dict[str, Any]
    usage: dict[str, Any]
    determinism_basis: str


class KimiAdvisoryError(RuntimeError):
    """Raised when the VLM advisory call fails or returns an unusable response.

    ``reason_code`` classifies the failure so the pipeline can fail closed with a
    faithful reason (a TRUNCATED read must never look like "found nothing").
    """

    def __init__(self, message: str, *, reason_code: ReasonCode = "TRANSPORT_ERROR") -> None:
        super().__init__(message)
        self.reason_code: ReasonCode = reason_code


def _reject_nonfinite(constant: str) -> float:
    # Strict JSON: NaN/Infinity are not allowed; a non-finite confidence would
    # otherwise slip past the abstention gate.
    raise ValueError(f"non-finite JSON constant not allowed: {constant}")


def _strip_json_fence(text: str) -> str:
    """Strip a leading ```json / ``` fence some servers emit even under json_object."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped[3:]
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    return stripped.strip()


class VlmAdvisoryClient:
    """OpenAI-compatible chat.completions client for advisory VLM reads."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str = "kimi-k3",
        profile: KimiModelProfile | None = None,
        reasoning_effort: str = "low",
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
        transport: Transport | None = None,
    ) -> None:
        if not base_url or not api_key:
            raise KimiAdvisoryError("VLM advisory client requires base_url and api_key")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._profile = profile or profile_for(model)
        self._model = self._profile.model_id
        self._reasoning_effort = reasoning_effort
        self._timeout = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._transport = transport or self._default_transport

    def __repr__(self) -> str:  # never leak the key
        return f"VlmAdvisoryClient(base_url={self._base_url!r}, model={self._model!r})"

    @property
    def determinism_basis(self) -> str:
        return self._profile.determinism_basis

    def _default_transport(self, url: str, headers: dict[str, str], body: bytes) -> bytes:
        from aerobim.core.security.outbound_url import safe_urlopen

        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        # safe_urlopen validates + DNS-pins + rejects redirects (allow_http=False).
        with safe_urlopen(request, timeout=self._timeout) as response:
            raw = response.read(self._max_response_bytes + 1)
        if len(raw) > self._max_response_bytes:
            raise KimiAdvisoryError(f"VLM response exceeds {self._max_response_bytes}-byte cap")
        return raw

    def _build_payload(
        self,
        data_url: str,
        *,
        sheet_id: str,
        prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        profile = self._profile
        payload: dict[str, Any] = {
            "model": self._model,
            "response_format": response_format or profile.response_format,
            # §2.5: never let the model run billable/uncontrolled server tools.
            "tools": [],
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an advisory drawing reader. Return ONLY JSON matching "
                        "the requested schema. You never decide compliance."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"sheet_id={sheet_id}\n{prompt}"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        }
        if profile.send_temperature:
            payload["temperature"] = 0
        if profile.supports_reasoning_effort:
            payload["reasoning_effort"] = self._reasoning_effort
        return payload

    def read_drawing(
        self,
        image_bytes: bytes,
        *,
        media_type: str,
        sheet_id: str,
        prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> KimiReadResult:
        """Send one image + prompt; return structured content + usage + basis.

        Grounding/verdict are the caller's job (``vlm_grounding``); this method
        only performs the transport, failure classification and JSON extraction.
        """

        data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        body = json.dumps(
            self._build_payload(
                data_url, sheet_id=sheet_id, prompt=prompt, response_format=response_format
            )
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        raw = self._transport(f"{self._base_url}/chat/completions", headers, body)
        try:
            envelope = json.loads(raw.decode("utf-8"), parse_constant=_reject_nonfinite)
        except (ValueError, UnicodeDecodeError) as exc:
            raise KimiAdvisoryError(
                f"VLM response is not valid JSON: {exc}", reason_code="SCHEMA_DEVIATION"
            ) from exc

        content = self._extract_message_content(envelope)
        if isinstance(content, dict):
            parsed: dict[str, Any] = content
        else:
            try:
                loaded = json.loads(_strip_json_fence(content), parse_constant=_reject_nonfinite)
            except ValueError as exc:
                raise KimiAdvisoryError(
                    f"VLM message content is not valid JSON: {exc}",
                    reason_code="SCHEMA_DEVIATION",
                ) from exc
            if not isinstance(loaded, dict):
                raise KimiAdvisoryError(
                    "VLM structured content must be a JSON object",
                    reason_code="SCHEMA_DEVIATION",
                )
            parsed = loaded

        usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
        return KimiReadResult(
            content=parsed, usage=dict(usage), determinism_basis=self._profile.determinism_basis
        )

    def _observations_response_format(self) -> dict[str, Any]:
        if self._profile.response_format.get("type") == "json_schema":
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "aerobim_region_observations",
                    "strict": True,
                    "schema": _OBSERVATIONS_SCHEMA,
                },
            }
        return {"type": "json_object"}

    def read_region(
        self,
        image_bytes: bytes,
        *,
        media_type: str,
        sheet_id: str,
        region_id: str,
        prompt: str,
    ) -> KimiReadResult:
        """Region-restricted read (§3/§4): one region crop → the observations schema."""
        return self.read_drawing(
            image_bytes,
            media_type=media_type,
            sheet_id=f"{sheet_id}#{region_id}",
            prompt=prompt,
            response_format=self._observations_response_format(),
        )

    @staticmethod
    def _extract_message_content(envelope: object) -> str | dict[str, Any]:
        if not isinstance(envelope, dict):
            raise KimiAdvisoryError(
                "VLM response envelope must be an object", reason_code="SCHEMA_DEVIATION"
            )
        choices = envelope.get("choices")
        if not isinstance(choices, list) or not choices:
            raise KimiAdvisoryError("VLM response has no choices", reason_code="SCHEMA_DEVIATION")
        first = choices[0] if isinstance(choices[0], dict) else {}
        # §2.4: a truncated JSON must be classified, never mistaken for "found nothing".
        if first.get("finish_reason") == "length":
            raise KimiAdvisoryError(
                "VLM response was truncated (finish_reason=length)", reason_code="TRUNCATED"
            )
        message = first.get("message") if isinstance(first.get("message"), dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, dict):
            return content
        if isinstance(content, str) and content.strip():
            return content
        # Thinking models may spend the budget on reasoning_content and return
        # empty content — that is EMPTY_CONTENT, distinct from a schema problem.
        has_reasoning = bool(message and str(message.get("reasoning_content") or "").strip())
        raise KimiAdvisoryError(
            "VLM response has empty content"
            + (" (reasoning_content present)" if has_reasoning else ""),
            reason_code="EMPTY_CONTENT",
        )


# Backwards-compatible alias (the class was formerly named KimiK3AdvisoryClient).
KimiK3AdvisoryClient = VlmAdvisoryClient

__all__ = [
    "KimiAdvisoryError",
    "KimiK3AdvisoryClient",
    "KimiModelProfile",
    "KimiReadResult",
    "ReasonCode",
    "Transport",
    "VlmAdvisoryClient",
    "kimi_k3_api_profile",
    "observations_schema_hash",
    "profile_for",
    "vllm_vlm_profile",
]
