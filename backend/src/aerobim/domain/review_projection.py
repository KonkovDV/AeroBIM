"""Overlay expert review onto serialized findings without touching ``summary.passed``.

Machine ``remark.body`` stays the engine text. Expert edits live in review-events
and are projected as ``issue["review"]`` for GET /v1/reports and final exports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aerobim.domain.models import ReviewEvent, ValidationIssue

_EVENT_TO_STATE: dict[str, str] = {
    "drawing_region_escalated": "escalated",
    "escalated": "escalated",
    "opened": "opened",
    "triaged": "opened",
    "accepted": "accepted",
    "rejected": "rejected",
    "edited": "edited",
    "edited_remark": "edited",
    "waived": "waived",
    "superseded": "superseded",
}
_NORM_PACK_EVENT_TYPES = frozenset({"norm_rule_proposed", "norm_rule_edited"})
_EDIT_EVENT_TYPES = frozenset({"edited_remark", "edited"})


def event_belongs_to_finding(
    event: ReviewEvent,
    *,
    finding_id: str | None,
    rule_id: str | None,
) -> bool:
    """Match by finding_id when the issue has one; otherwise by rule_id."""

    if event.event_type in _NORM_PACK_EVENT_TYPES:
        return False
    fid = (finding_id or "").strip() or None
    event_fid = (event.finding_id or "").strip() or None
    if fid is not None:
        return event_fid == fid
    rid = (rule_id or "").strip() or None
    event_rid = (event.issue_rule_id or "").strip() or None
    return rid is not None and event_rid == rid


def project_issue_review(
    *,
    finding_id: str | None,
    rule_id: str | None,
    machine_text: str | None,
    events: Sequence[ReviewEvent],
) -> dict[str, Any]:
    """Build the public review overlay for one finding. Never writes a verdict."""

    state: str | None = None
    actor: str | None = None
    event_id: str | None = None
    effective = machine_text
    for event in events:
        if not event_belongs_to_finding(event, finding_id=finding_id, rule_id=rule_id):
            continue
        mapped = (event.resulting_state or "").strip() or _EVENT_TO_STATE.get(event.event_type)
        if mapped:
            state = mapped
            actor = event.actor
            event_id = event.event_id
        if event.event_type in _EDIT_EVENT_TYPES and (event.note or "").strip():
            effective = event.note
    return {
        "effective_text": effective,
        "state": state,
        "actor": actor,
        "event_id": event_id,
        "machine_text": machine_text,
    }


def _machine_text_from_issue_dict(issue: Mapping[str, Any]) -> str | None:
    remark = issue.get("remark")
    if isinstance(remark, Mapping):
        body = remark.get("body")
        if body is None:
            return None
        return str(body)
    return None


def attach_review_projection(
    issues: Sequence[Any],
    events: Sequence[ReviewEvent],
) -> list[Any]:
    """Copy issue dicts and attach ``review`` without mutating machine remark."""

    projected: list[Any] = []
    for issue in issues:
        if not isinstance(issue, dict):
            projected.append(issue)
            continue
        cloned = dict(issue)
        cloned["review"] = project_issue_review(
            finding_id=str(issue["finding_id"]) if issue.get("finding_id") else None,
            rule_id=str(issue["rule_id"]) if issue.get("rule_id") else None,
            machine_text=_machine_text_from_issue_dict(issue),
            events=events,
        )
        projected.append(cloned)
    return projected


def effective_text_for_issue(
    issue: ValidationIssue,
    events: Sequence[ReviewEvent] | None,
) -> str:
    """BCF Description: expert edit when present, else machine remark/message."""

    machine = issue.remark.body if issue.remark is not None else (issue.message or "")
    if not events:
        return machine
    overlay = project_issue_review(
        finding_id=issue.finding_id,
        rule_id=issue.rule_id,
        machine_text=issue.remark.body if issue.remark is not None else None,
        events=events,
    )
    text = overlay.get("effective_text")
    if isinstance(text, str) and text.strip():
        return text
    return machine


__all__ = [
    "attach_review_projection",
    "effective_text_for_issue",
    "event_belongs_to_finding",
    "project_issue_review",
]
