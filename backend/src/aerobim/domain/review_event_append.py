"""Locked HITL review-event append contract (RT-AUDIT-001)."""

from __future__ import annotations

from dataclasses import dataclass

from aerobim.domain.models import ReviewEvent, ValidationReport


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
    expected_review_version: int | None = None


def append_payload_fingerprint(spec: ReviewEventAppendSpec) -> str:
    """Canonical payload for idempotent replay. Created_at is excluded."""

    return "|".join(
        (
            spec.event_type,
            (spec.finding_id or "").strip(),
            (spec.issue_rule_id or "").strip(),
            (spec.note or "").strip(),
            (spec.actor or "").strip(),
            (spec.previous_state or "").strip(),
        )
    )


def stored_event_payload_fingerprint(event: ReviewEvent) -> str:
    return "|".join(
        (
            event.event_type,
            (event.finding_id or "").strip(),
            (event.issue_rule_id or "").strip(),
            (event.note or "").strip(),
            (event.actor or "").strip(),
            (event.previous_state or "").strip(),
        )
    )


def latest_finding_sequence(
    events: list[ReviewEvent],
    *,
    finding_id: str | None,
    issue_rule_id: str | None,
) -> int | None:
    """Last sequence_number for this finding; not the last event of the whole report."""

    fid = (finding_id or "").strip() or None
    rid = (issue_rule_id or "").strip() or None
    latest: int | None = None
    for event in events:
        event_fid = (event.finding_id or "").strip() or None
        event_rid = (event.issue_rule_id or "").strip() or None
        if fid is not None:
            if event_fid != fid:
                continue
        elif rid is not None:
            if event_rid != rid:
                continue
        else:
            continue
        if event.sequence_number is not None:
            latest = event.sequence_number
    return latest


def assert_review_target_in_report(
    report: ValidationReport,
    *,
    finding_id: str | None,
    issue_rule_id: str | None,
) -> None:
    """Reject events that name a finding/rule not present on the authorized report."""

    if not report.issues:
        return
    fid = (finding_id or "").strip()
    rid = (issue_rule_id or "").strip()
    if fid:
        matches = [issue for issue in report.issues if (issue.finding_id or "").strip() == fid]
        if not matches:
            raise ValueError("finding_id is not a member of this report")
        if rid and any((issue.rule_id or "").strip() != rid for issue in matches):
            raise ValueError("issue_rule_id does not match finding_id on this report")
        return
    if rid:
        matches = [issue for issue in report.issues if (issue.rule_id or "").strip() == rid]
        if len(matches) != 1:
            raise ValueError("issue_rule_id is missing or not unique on this report")


__all__ = [
    "HitlStateConflictError",
    "ReviewEventAppendSpec",
    "append_payload_fingerprint",
    "assert_review_target_in_report",
    "latest_finding_sequence",
    "stored_event_payload_fingerprint",
]
