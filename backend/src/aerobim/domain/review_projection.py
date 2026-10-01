"""Overlay expert review onto serialized findings without touching ``summary.passed``.

Machine ``remark.body`` stays the engine text. Expert edits live in review-events
and are projected as ``issue["review"]`` for GET /v1/reports and final exports.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

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


ReviewPartition = Literal["confirmed", "rejected", "edited", "untouched"]


def partition_from_state(state: str | None) -> ReviewPartition:
    """Map a review overlay state onto the four export buckets."""

    if state == "rejected":
        return "rejected"
    if state == "edited":
        return "edited"
    if state == "accepted":
        return "confirmed"
    return "untouched"


def review_partition_of(issue: Any) -> ReviewPartition:
    """Partition one serialized issue (or ValidationIssue) by expert state."""

    if isinstance(issue, Mapping):
        review = issue.get("review")
        state = str(review.get("state") or "") if isinstance(review, Mapping) else ""
        return partition_from_state(state or None)
    review = getattr(issue, "review", None)
    if isinstance(review, Mapping):
        return partition_from_state(str(review.get("state") or "") or None)
    return "untouched"


def review_partition(issues: Sequence[Any]) -> dict[ReviewPartition, list[Any]]:
    """Split issues into confirmed / rejected / edited / untouched lists."""

    buckets: dict[ReviewPartition, list[Any]] = {
        "confirmed": [],
        "rejected": [],
        "edited": [],
        "untouched": [],
    }
    for item in issues:
        buckets[review_partition_of(item)].append(item)
    return buckets


def issue_is_rejected(
    issue: ValidationIssue,
    events: Sequence[ReviewEvent] | None,
) -> bool:
    """True when the latest review event for this finding is a rejection."""

    if not events:
        return False
    overlay = project_issue_review(
        finding_id=issue.finding_id,
        rule_id=issue.rule_id,
        machine_text=issue.remark.body if issue.remark is not None else None,
        events=events,
    )
    return partition_from_state(str(overlay.get("state") or "") or None) == "rejected"


_HITL_BCF_COMMENT_TYPES = frozenset(
    {
        "opened",
        "accepted",
        "rejected",
        "edited",
        "edited_remark",
        "triaged",
        "waived",
        "escalated",
    }
)
_BCF_CLOSED_STATES = frozenset({"accepted", "waived"})
_MACHINE_BCF_AUTHOR = "aerobim-backend"


@dataclass(frozen=True)
class BcfHitlComment:
    """One HITL event as a BCF Comment (Date/Author/Comment). Not a verdict."""

    event_id: str
    date: str
    author: str
    text: str
    event_type: str


@dataclass(frozen=True)
class BcfHitlOverlay:
    """TopicStatus / Modified* / Comment* derived from review events.

    CreationAuthor stays the machine. Expert identity lives in Comment Author
    and ModifiedAuthor. Never writes ``summary.passed``.
    """

    topic_status: str
    modified_author: str | None
    modified_date: str | None
    comments: tuple[BcfHitlComment, ...]


def bcf_hitl_overlay(
    issue: ValidationIssue,
    events: Sequence[ReviewEvent] | None,
) -> BcfHitlOverlay:
    """Map HITL events onto BCF TopicStatus, ModifiedAuthor, and comments."""

    if not events:
        return BcfHitlOverlay(
            topic_status="Open",
            modified_author=None,
            modified_date=None,
            comments=(),
        )
    comments: list[BcfHitlComment] = []
    for event in events:
        if not event_belongs_to_finding(event, finding_id=issue.finding_id, rule_id=issue.rule_id):
            continue
        if event.event_type not in _HITL_BCF_COMMENT_TYPES:
            continue
        note = (event.note or "").strip()
        text = note if note else f"event_type={event.event_type}"
        fid = (issue.finding_id or "").strip()
        if fid and f"finding_id={fid}" not in text:
            text = f"{text}\nfinding_id={fid}"
        comments.append(
            BcfHitlComment(
                event_id=event.event_id,
                date=event.created_at,
                author=(event.actor or "").strip() or _MACHINE_BCF_AUTHOR,
                text=text,
                event_type=event.event_type,
            )
        )
    overlay = project_issue_review(
        finding_id=issue.finding_id,
        rule_id=issue.rule_id,
        machine_text=issue.remark.body if issue.remark is not None else None,
        events=events,
    )
    state = str(overlay.get("state") or "") or None
    status = "Closed" if state in _BCF_CLOSED_STATES else "Open"
    actor = overlay.get("actor")
    modified_author = str(actor).strip() if isinstance(actor, str) and actor.strip() else None
    modified_date = comments[-1].date if comments else None
    return BcfHitlOverlay(
        topic_status=status,
        modified_author=modified_author,
        modified_date=modified_date,
        comments=tuple(comments),
    )


__all__ = [
    "BcfHitlComment",
    "BcfHitlOverlay",
    "attach_review_projection",
    "bcf_hitl_overlay",
    "effective_text_for_issue",
    "event_belongs_to_finding",
    "issue_is_rejected",
    "partition_from_state",
    "project_issue_review",
    "review_partition",
    "review_partition_of",
]
