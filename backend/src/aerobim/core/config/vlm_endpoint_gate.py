"""Fail-closed gates for VLM endpoint / model pairing."""

from __future__ import annotations

from urllib.parse import urlparse

_YANDEX_KIMI_REFUSAL = (
    "Yandex Studio requires AEROBIM_VLM_MODEL or AEROBIM_LLM_MODEL "
    "(e.g. gpt://<folder>/qwen3.6-35b-a3b); kimi-k3 default is refused"
)

# Hosts that clearly belong to a non-Yandex VLM vendor / lab fixture.
# Ambient AEROBIM_LLM_PROVIDER=yandex must not poison these smoke URLs.
_NON_YANDEX_HOST_MARKERS = (
    "kimi",
    "moonshot",
    "openai",
    "anthropic",
    "localhost",
    "127.0.0.1",
    "example.",
    "invalid",
)


def endpoint_looks_like_yandex(
    base_url: str | None,
    *,
    provider: str | None = None,
) -> bool:
    """True when the VLM URL / provider indicates Yandex AI Studio contour.

    - Hostname containing ``yandex`` → Yandex.
    - Explicit non-Yandex host markers win over ambient ``AEROBIM_LLM_PROVIDER``.
    - Provider ``yandex*`` with empty host, IP, or unknown CDN host → Yandex
      (closes IP/proxy bypass of the kimi-k3 refuse gate).
    """

    host = ""
    if base_url:
        try:
            host = (urlparse(base_url).hostname or "").lower()
        except Exception:  # noqa: BLE001 — malformed URL → empty host
            host = ""
    if "yandex" in host:
        return True
    provider_yandex = (provider or "").strip().lower().startswith("yandex")
    if not provider_yandex:
        return False
    if not host:
        return True
    if any(marker in host for marker in _NON_YANDEX_HOST_MARKERS):
        return False
    return True


def refuse_yandex_kimi_default_model(
    *,
    base_url: str | None,
    model: str | None,
    provider: str | None = None,
) -> str | None:
    """Return a refusal reason when Yandex would get the kimi-k3 request profile.

    Silent kimi-k3 against Yandex Studio uses the wrong response_format /
    reasoning_effort shape. Mentor demo, DI ready-gate, and smoke CLIs share
    this check.
    """

    mid = (model or "").strip().lower()
    if endpoint_looks_like_yandex(base_url, provider=provider) and (
        not mid or mid.startswith("kimi-k3")
    ):
        return _YANDEX_KIMI_REFUSAL
    return None


__all__ = [
    "endpoint_looks_like_yandex",
    "refuse_yandex_kimi_default_model",
]
