"""Tamper-evidence hash chain for HITL review events (RT-AUDIT-002)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

from aerobim.domain.models import ReviewEvent

_GENESIS = "genesis"


def review_event_content_hash(
    event: ReviewEvent,
    *,
    previous_event_hash: str,
) -> str:
    """SHA-256 over canonical event payload + previous hash (not a signature)."""

    payload = {
        "event_id": event.event_id,
        "report_id": event.report_id,
        "event_type": event.event_type,
        "created_at": event.created_at,
        "sequence_number": event.sequence_number,
        "previous_state": event.previous_state,
        "resulting_state": event.resulting_state,
        "finding_id": event.finding_id,
        "issue_rule_id": event.issue_rule_id,
        "actor": event.actor,
        "note": event.note,
        "idempotency_key": event.idempotency_key,
        "previous_event_hash": previous_event_hash or _GENESIS,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def genesis_previous_hash() -> str:
    return _GENESIS


__all__ = ["genesis_previous_hash", "review_event_content_hash"]
