"""Aggregate HITL review KPIs from persisted review events."""

from __future__ import annotations

from collections import Counter

from aerobim.domain.models import ReviewEvent


def summarize_review_events(events: list[ReviewEvent]) -> dict[str, object]:
    counts = Counter(event.event_type for event in events)
    latencies = [e.latency_ms for e in events if e.latency_ms is not None]
    accepted = counts.get("accepted", 0)
    rejected = counts.get("rejected", 0)
    decided = accepted + rejected
    acceptance_rate = (accepted / decided) if decided else None
    avg_latency = (sum(latencies) / len(latencies)) if latencies else None
    return {
        "event_count": len(events),
        "by_type": dict(counts),
        "acceptance_rate": acceptance_rate,
        "avg_latency_ms": avg_latency,
        "opened_count": counts.get("opened", 0),
        "triaged_count": counts.get("triaged", 0),
    }
