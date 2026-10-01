"""Typed, tamper-evident audit event for the Hybrid AI routing contour (§13, P0.8).

Records the FULL route path for one hybrid decision so audit can answer «who sent
what, where did it go, why this route, what was removed/sent, which model, was it
cached/changed, did it pass verification, was a human called, did it affect the
verdict». Domain-pure: no I/O, no verdict impact (``verdict_impact`` is always
``"none"`` — ADR-001).

Honesty / secret-safety (§13 «нельзя писать в аудит», §25):
- Only HASHES of content are stored (input/payload/crop/prompt/response), never raw
  documents or ``reasoning_content``.
- Forbidden keys (api_key/token/secret/password/authorization/reasoning_content/...)
  are stripped from any free-form ``usage``/metadata and the serializer FAILS CLOSED
  (raises) if any forbidden key still slips through.
- ``event_content_hash`` is a content-integrity hash (tamper-evidence), not a
  cryptographic signature.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from aerobim.domain.hybrid.trust_policy import RouteDecision, RouteStatus
from aerobim.domain.vlm_cache import content_sha256

# Keys that must never appear in an audit record (case-insensitive).
_FORBIDDEN_AUDIT_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "x_api_key",
        "authorization",
        "bearer",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "session_token",
        "secret",
        "secret_key",
        "client_secret",
        "password",
        "credential",
        "credentials",
        "private_key",
        "reasoning_content",
    }
)
_NON_ALNUM = re.compile(r"[^a-z0-9]")


def _normalize_key(key: object) -> str:
    """Lowercase + strip separators so api-key / x_api_key / apiKey all collapse."""
    return _NON_ALNUM.sub("", str(key).lower())


_FORBIDDEN_NORMALIZED = frozenset(_normalize_key(k) for k in _FORBIDDEN_AUDIT_KEYS)


def _is_forbidden_key(key: object) -> bool:
    return _normalize_key(key) in _FORBIDDEN_NORMALIZED


def _redact_value(value: Any) -> Any:
    """Recurse into mappings AND lists/tuples so list-nested secrets are redacted."""
    if isinstance(value, Mapping):
        return redact_audit_fields(value)
    if isinstance(value, (list, tuple)):
        return [_redact_value(item) for item in value]
    return value


_STATUS_TIER = {
    RouteStatus.LOCAL: "local",
    RouteStatus.PRIVATE: "private",
    RouteStatus.PUBLIC_MASKED: "public",
    RouteStatus.BLOCKED: "none",
    RouteStatus.HUMAN_REVIEW: "none",
}


class AuditSecretLeakError(RuntimeError):
    """Raised when a forbidden (secret) key would be written to an audit record."""


def redact_audit_fields(fields: Mapping[str, Any] | None) -> dict[str, Any]:
    """Drop forbidden keys (normalized) recursively, incl. list-nested mappings."""
    if not fields:
        return {}
    safe: dict[str, Any] = {}
    for key, value in fields.items():
        if _is_forbidden_key(key):
            continue
        safe[str(key)] = _redact_value(value)
    return safe


@dataclass(frozen=True)
class HybridAuditEvent:
    """Typed audit record for one hybrid route decision (§13)."""

    event_id: str
    timestamp: str
    request_id: str
    tenant_id: str
    classification: str
    task_type: str
    route_status: str
    final_route_status: str
    tier: str
    policy_version: str
    human_review_required: bool
    cache_hit: bool
    project_id: str | None = None
    principal_id: str | None = None
    document_id: str | None = None
    source_id: str | None = None
    model_provider: str | None = None
    model_id: str | None = None
    model_snapshot: str | None = None
    endpoint: str | None = None
    fields_sent: tuple[str, ...] = ()
    fields_removed: tuple[str, ...] = ()
    mask_version: str | None = None
    input_hash: str | None = None
    payload_hash: str | None = None
    crop_hash: str | None = None
    prompt_hash: str | None = None
    schema_hash: str | None = None
    normalizer_version: str | None = None
    cache_key: str | None = None
    cache_namespace: str | None = None
    response_hash: str | None = None
    usage: Mapping[str, Any] | None = None
    latency_ms: float | None = None
    cost: float | None = None
    failure_reason: str | None = None
    # Hybrid AI never decides the engineering verdict (ADR-001). init=False makes it
    # structurally unbypassable — not even via direct construction.
    verdict_impact: str = field(default="none", init=False)

    def to_audit_dict(self) -> dict[str, Any]:
        """JSON-safe record; redacts ``usage`` and FAILS CLOSED on any forbidden key."""
        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "principal_id": self.principal_id,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "classification": self.classification,
            "task_type": self.task_type,
            "route_status": self.route_status,
            "final_route_status": self.final_route_status,
            "tier": self.tier,
            "policy_version": self.policy_version,
            "human_review_required": self.human_review_required,
            "cache_hit": self.cache_hit,
            "model_provider": self.model_provider,
            "model_id": self.model_id,
            "model_snapshot": self.model_snapshot,
            "endpoint": self.endpoint,
            "fields_sent": list(self.fields_sent),
            "fields_removed": list(self.fields_removed),
            "mask_version": self.mask_version,
            "input_hash": self.input_hash,
            "payload_hash": self.payload_hash,
            "crop_hash": self.crop_hash,
            "prompt_hash": self.prompt_hash,
            "schema_hash": self.schema_hash,
            "normalizer_version": self.normalizer_version,
            "cache_key": self.cache_key,
            "cache_namespace": self.cache_namespace,
            "response_hash": self.response_hash,
            "usage": redact_audit_fields(self.usage),
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "failure_reason": self.failure_reason,
            "verdict_impact": self.verdict_impact,
        }
        _assert_no_forbidden_keys(payload)
        return payload

    def event_content_hash(self) -> str:
        """Content-integrity hash over the record (tamper-evidence, not a signature)."""
        return content_sha256(self.to_audit_dict())


def _assert_no_forbidden_keys(payload: Mapping[str, Any]) -> None:
    for key, value in payload.items():
        if _is_forbidden_key(key):
            raise AuditSecretLeakError(f"forbidden key in audit record: {key!r}")
        _assert_value_has_no_forbidden_keys(value)


def _assert_value_has_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        _assert_no_forbidden_keys(value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_value_has_no_forbidden_keys(item)


def build_route_audit_event(
    *,
    event_id: str,
    timestamp: str,
    request_id: str,
    tenant_id: str,
    task_type: str,
    decision: RouteDecision,
    policy_version: str = "1.0.0",
    failure_reason: str | None = None,
    **metadata: Any,
) -> HybridAuditEvent:
    """Build an audit event from a :class:`RouteDecision` (verdict_impact fixed none).

    Extra ``metadata`` (project_id, hashes, model_*, usage, ...) is accepted but
    passed through the dataclass fields only; ``usage`` is redacted on serialization.
    ``human_review_required`` is derived from the decision status.
    """
    tier = _STATUS_TIER.get(decision.status, "none")
    # Fields set explicitly below (or fixed) must never be overridden via metadata.
    explicit = {
        "event_id",
        "timestamp",
        "request_id",
        "tenant_id",
        "classification",
        "task_type",
        "route_status",
        "final_route_status",
        "tier",
        "policy_version",
        "human_review_required",
        "cache_hit",
        "failure_reason",
        "verdict_impact",
    }
    allowed_fields = HybridAuditEvent.__dataclass_fields__
    safe_meta = {k: v for k, v in metadata.items() if k in allowed_fields and k not in explicit}
    # Redact secrets at CONSTRUCTION (not only at serialization) so the in-memory
    # event / its repr / asdict can never carry a secret (Red Team MEDIUM).
    usage_meta = safe_meta.get("usage")
    if isinstance(usage_meta, Mapping):
        safe_meta["usage"] = redact_audit_fields(usage_meta)
    return HybridAuditEvent(
        event_id=event_id,
        timestamp=timestamp,
        request_id=request_id,
        tenant_id=tenant_id,
        classification=decision.classification.value,
        task_type=task_type,
        route_status=decision.status.value,
        final_route_status=decision.status.value,
        tier=tier,
        policy_version=policy_version,
        human_review_required=decision.status is RouteStatus.HUMAN_REVIEW,
        cache_hit=bool(metadata.get("cache_hit", False)),
        failure_reason=(
            failure_reason or (decision.reason if decision.status is RouteStatus.BLOCKED else None)
        ),
        **safe_meta,
    )


__all__ = [
    "AuditSecretLeakError",
    "HybridAuditEvent",
    "build_route_audit_event",
    "redact_audit_fields",
]
