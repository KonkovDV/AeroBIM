"""Kimi K3 / Kimi-VL advisory client — OpenAI-compatible, SSRF-guarded.

Advisory only (ADR-001 / TR-31): returns a raw structured response for
``vlm_grounding`` to turn into **candidate** regions. It never decides a verdict.

Security posture:
- outbound goes through the shared SSRF guard (``safe_urlopen``): DNS pinned,
  redirects rejected, private/metadata IPs blocked;
- the response body is read with a byte cap (oversized → error, no unbounded
  buffering);
- the API key travels only in the Authorization header and is redacted from
  ``repr`` / logs;
- ``temperature=0`` for reproducible eval runs (VLM comparison protocol).

The ``transport`` seam is injectable so tests never touch the network.
"""

from __future__ import annotations

import base64
import json
import urllib.request
from collections.abc import Callable
from typing import Any

_DEFAULT_TIMEOUT_SECONDS = 60.0
_DEFAULT_MAX_RESPONSE_BYTES = 4 * 1024 * 1024

# transport(url, headers, body) -> response bytes
Transport = Callable[[str, dict[str, str], bytes], bytes]


def _reject_nonfinite(constant: str) -> float:
    # Strict JSON (constrained-decoding posture): NaN/Infinity are not allowed;
    # a non-finite confidence would otherwise slip past the abstention gate.
    raise ValueError(f"non-finite JSON constant not allowed: {constant}")


class KimiAdvisoryError(RuntimeError):
    """Raised when the Kimi advisory call fails or returns an unusable response."""


class KimiK3AdvisoryClient:
    """Minimal OpenAI-compatible chat.completions client for advisory VLM reads."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str = "kimi-k3",
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
        transport: Transport | None = None,
    ) -> None:
        if not base_url or not api_key:
            raise KimiAdvisoryError("Kimi advisory client requires base_url and api_key")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._transport = transport or self._default_transport

    def __repr__(self) -> str:  # never leak the key
        return f"KimiK3AdvisoryClient(base_url={self._base_url!r}, model={self._model!r})"

    def _default_transport(self, url: str, headers: dict[str, str], body: bytes) -> bytes:
        from aerobim.core.security.outbound_url import safe_urlopen

        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        # safe_urlopen validates + DNS-pins + rejects redirects (allow_http=False).
        with safe_urlopen(request, timeout=self._timeout) as response:
            raw = response.read(self._max_response_bytes + 1)
        if len(raw) > self._max_response_bytes:
            raise KimiAdvisoryError(f"Kimi response exceeds {self._max_response_bytes}-byte cap")
        return raw

    def read_drawing(
        self,
        image_bytes: bytes,
        *,
        media_type: str,
        sheet_id: str,
        prompt: str,
    ) -> dict[str, Any]:
        """Send one image + prompt; return the parsed structured JSON payload.

        Grounding/verdict are the caller's job (``vlm_grounding``); this method
        only performs the transport and JSON extraction.
        """

        data_url = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        payload = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
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
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self._base_url}/chat/completions"

        raw = self._transport(url, headers, body)
        try:
            envelope = json.loads(raw.decode("utf-8"), parse_constant=_reject_nonfinite)
        except (ValueError, UnicodeDecodeError) as exc:
            raise KimiAdvisoryError(f"Kimi response is not valid JSON: {exc}") from exc
        content = self._extract_message_content(envelope)
        try:
            parsed = json.loads(content, parse_constant=_reject_nonfinite)
        except ValueError as exc:
            raise KimiAdvisoryError(f"Kimi message content is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise KimiAdvisoryError("Kimi structured content must be a JSON object")
        return parsed

    @staticmethod
    def _extract_message_content(envelope: object) -> str:
        if not isinstance(envelope, dict):
            raise KimiAdvisoryError("Kimi response envelope must be an object")
        choices = envelope.get("choices")
        if not isinstance(choices, list) or not choices:
            raise KimiAdvisoryError("Kimi response has no choices")
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise KimiAdvisoryError("Kimi response choice has no message content")
        return content


__all__ = ["KimiAdvisoryError", "KimiK3AdvisoryClient", "Transport"]
