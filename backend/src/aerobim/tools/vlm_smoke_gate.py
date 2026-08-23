"""Shared HybridRouteGate pre-check for opt-in VLM smoke tools (residual RT-WP02-03).

Smoke paths that call an external VLM MUST evaluate the gate before constructing
clients. Fail-closed: empty tenant / blocked route / PUBLIC without mask → no
egress. Open-data smoke uses ``public_fixture`` + PUBLIC + PrivacyGuard.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Mapping
from typing import Any

from aerobim.application.services.hybrid_route_gate import HybridGateResult, HybridRouteGate
from aerobim.domain.hybrid.privacy_guard import PrivacyGuard
from aerobim.domain.hybrid.trust_policy import RouteTarget

DEFAULT_SMOKE_TENANT = "open-data-smoke"
DEFAULT_SMOKE_OBJECT_KIND = "public_fixture"
_DEFAULT_MASK_RULES: dict[str, str] = {
    "sheet_id": "keep",
    "image_name": "keep",
    "purpose": "keep",
}


def smoke_tenant_id(explicit: str | None = None) -> str:
    """Resolve tenant. ``None`` → default; explicit empty string stays empty (blocks)."""

    if explicit is None:
        return (os.getenv("AEROBIM_HYBRID_SMOKE_TENANT") or DEFAULT_SMOKE_TENANT).strip()
    return explicit.strip()


def build_vlm_smoke_gate(*, tenant_salt: str | None = None) -> HybridRouteGate:
    salt = (
        tenant_salt or os.getenv("AEROBIM_HYBRID_TENANT_SALT") or "smoke-open-data-salt"
    ).strip()
    return HybridRouteGate(privacy_guard=PrivacyGuard(tenant_salt=salt))


def evaluate_vlm_smoke_egress(
    *,
    tenant_id: str,
    sheet_id: str,
    image_name: str,
    gate: HybridRouteGate | None = None,
    object_kind: str = DEFAULT_SMOKE_OBJECT_KIND,
    target: RouteTarget = RouteTarget.PUBLIC,
    request_id: str | None = None,
    extra_payload: Mapping[str, Any] | None = None,
) -> HybridGateResult:
    """Gate before any VLM client construction. PUBLIC open-data requires masking."""

    payload: dict[str, Any] = {
        "sheet_id": sheet_id,
        "image_name": image_name,
        "purpose": "tier_a_open_data_vlm_smoke",
    }
    if extra_payload:
        payload.update(dict(extra_payload))

    active = gate or build_vlm_smoke_gate()
    return active.evaluate(
        object_kind=object_kind,
        target=target,
        tenant_id=tenant_id,
        task_type="vlm_smoke_egress",
        request_id=request_id or f"smoke-{uuid.uuid4().hex[:12]}",
        payload=payload,
        mask_rules=_DEFAULT_MASK_RULES,
        owner_consent=False,
        private_mode_confirmed=False,
    )


def gate_blocks_external(result: HybridGateResult) -> bool:
    """True when smoke must not call the VLM client."""

    return not result.may_call_external


def smoke_signoff_blocks_external(*, settings: Any | None = None) -> str | None:
    """Fail-closed: pilot/production must not run external VLM smoke CLIs.

    Product DI already gates via ``Settings.vlm_advisory_ready()``. Smoke tools
    historically skip ``vlm_enabled`` (operator opt-in by running the tool) but
    MUST still honour the closed-contour signoff profiles.

    Reads ``AEROBIM_SIGNOFF_PROFILE`` directly when ``settings`` is omitted so
    unit tests / partial env do not trigger full ``Settings.from_env()`` SSRF
    validation just to check the profile gate.
    Returns a human reason when blocked, else ``None``.
    """

    if settings is None:
        profile = (os.getenv("AEROBIM_SIGNOFF_PROFILE") or "dev").strip().lower() or "dev"
    else:
        profile = (getattr(settings, "signoff_profile", None) or "dev").strip().lower()
    from aerobim.application.services.capability_policy import (
        is_closed_egress_profile,
        normalize_signoff_profile,
    )

    canonical = normalize_signoff_profile(profile)
    if is_closed_egress_profile(canonical):
        return (
            f"signoff_profile={canonical!r} forbids external VLM smoke egress "
            "(use open-data/dev profile or the DI path with vlm_advisory_ready)"
        )
    return None


__all__ = [
    "DEFAULT_SMOKE_OBJECT_KIND",
    "DEFAULT_SMOKE_TENANT",
    "build_vlm_smoke_gate",
    "evaluate_vlm_smoke_egress",
    "gate_blocks_external",
    "smoke_signoff_blocks_external",
    "smoke_tenant_id",
]
