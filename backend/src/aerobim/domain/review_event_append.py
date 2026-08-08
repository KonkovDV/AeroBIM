"""Locked HITL review-event append contract (RT-AUDIT-001)."""

from __future__ import annotations

from dataclasses import dataclass


class HitlStateConflictError(ValueError):
    """Optimistic concurrency: client previous_state does not match server SSOT."""


@dataclass(frozen=True)
class ReviewEventAppendSpec:
    """Input for store-level locked append (HTTP route delegates here)."""

    report_id: str
    event_type: str
    created_at: str
    actor: str | None = None
    note: str | None = None
    latency_ms: int | None = None
    issue_rule_id: str | None = None
    finding_id: str | None = None
    previous_state: str | None = None
    idempotency_key: str | None = None
    event_id: str | None = None


__all__ = ["HitlStateConflictError", "ReviewEventAppendSpec"]
