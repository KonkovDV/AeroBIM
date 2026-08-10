"""Fail-closed gates for VLM endpoint / model pairing."""

from __future__ import annotations

from urllib.parse import urlparse

_YANDEX_KIMI_REFUSAL = (
    "Yandex Studio requires AEROBIM_VLM_MODEL or AEROBIM_LLM_MODEL "
    "(e.g. gpt://<folder>/qwen3.6-35b-a3b); kimi-k3 default is refused"
)


def endpoint_looks_like_yandex(
    base_url: str | None,
    *,
    provider: str | None = None,
) -> bool:
    """True when the VLM base URL (or URL-less provider) indicates Yandex Studio.

    Provider alone must not override an explicit non-Yandex ``base_url`` — ambient
    ``AEROBIM_LLM_PROVIDER`` must not poison Kimi/vLLM smoke against other hosts.
    """

    host = ""
    if base_url:
        try:
            host = (urlparse(base_url).hostname or "").lower()
        except Exception:  # noqa: BLE001 — malformed URL → empty host
            host = ""
    if "yandex" in host:
        return True
    if host:
        return False
    return (provider or "").strip().lower().startswith("yandex")


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
