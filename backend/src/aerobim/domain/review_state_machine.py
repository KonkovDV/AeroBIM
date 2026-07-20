"""HITL finding review state machine (RT-HYPER lifecycle).

System escalations are distinct from expert decisions. Invalid transitions fail closed.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol

HitlReviewState = Literal[
    "escalated",
    "opened",
    "accepted",
    "rejected",
    "edited",
    "waived",
    "superseded",
]

HITL_REVIEW_STATES: frozenset[str] = frozenset(
    {"escalated", "opened", "accepted", "rejected", "edited", "waived", "superseded"}
)

# Map legacy ReviewEvent.event_type values onto the finding lifecycle.
_EVENT_TO_STATE: dict[str, HitlReviewState] = {
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

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "escalated": frozenset({"opened", "superseded"}),
    "opened": frozenset({"accepted", "rejected", "edited", "waived", "superseded"}),
    "edited": frozenset({"accepted", "rejected", "waived", "opened", "superseded"}),
    "accepted": frozenset({"superseded"}),
    "rejected": frozenset({"opened", "superseded"}),
    "waived": frozenset({"superseded"}),
    "superseded": frozenset(),
}


class HitlTransitionError(ValueError):
    """Invalid HITL lifecycle transition or missing required fields."""


class _HitlEventLike(Protocol):
    event_type: str
    finding_id: str | None
    issue_rule_id: str | None
    resulting_state: str | None


_NORM_PACK_EVENT_TYPES = frozenset({"norm_rule_proposed", "norm_rule_edited"})


def latest_hitl_state(
    events: Sequence[_HitlEventLike],
    finding_id: str | None,
    issue_rule_id: str | None,
) -> str | None:
    """Return server SSOT HITL state for a finding/issue from stored events.

    Walks events in order and keeps the last ``resulting_state`` matching the
    finding (preferred) or issue rule. Norm-pack events are ignored.
    """

    fid = (finding_id or "").strip() or None
    rid = (issue_rule_id or "").strip() or None
    latest: str | None = None
    for event in events:
        if event.event_type in _NORM_PACK_EVENT_TYPES:
            continue
        event_fid = (getattr(event, "finding_id", None) or "").strip() or None
        event_rid = (getattr(event, "issue_rule_id", None) or "").strip() or None
        if fid is not None:
            if event_fid != fid:
                continue
        elif rid is not None:
            if event_rid != rid:
                continue
        state = (getattr(event, "resulting_state", None) or "").strip() or None
        if state:
            latest = state
    return latest


def normalize_hitl_state(event_type: str) -> HitlReviewState:
    state = _EVENT_TO_STATE.get(event_type)
    if state is None:
        raise HitlTransitionError(f"Unknown HITL event_type: {event_type}")
    return state


def assert_hitl_transition(
    *,
    current: str | None,
    event_type: str,
    actor: str | None = None,
    note: str | None = None,
) -> HitlReviewState:
    """Validate transition and mandatory actor/reason rules.

    - ``accepted → opened`` is forbidden (must use explicit reopen via ``rejected → opened``
      or supersede).
    - ``edited`` requires a non-empty actor.
    - ``waived`` requires a non-empty reason/note.
    - ``accepted`` / ``rejected`` / ``waived`` / ``edited`` from system actor are forbidden.
    """

    target = normalize_hitl_state(event_type)
    if current is None:
        if target != "escalated" and target != "opened":
            raise HitlTransitionError(
                f"Initial HITL state must be escalated or opened, got {target}"
            )
        _assert_actor_rules(target, actor=actor, note=note)
        return target

    current_norm = normalize_hitl_state(current) if current in _EVENT_TO_STATE else current
    if current_norm not in HITL_REVIEW_STATES:
        raise HitlTransitionError(f"Unknown current HITL state: {current}")
    allowed = _ALLOWED_TRANSITIONS[current_norm]
    if target not in allowed:
        raise HitlTransitionError(
            f"Illegal HITL transition {current_norm} → {target}; allowed={sorted(allowed)}"
        )
    _assert_actor_rules(target, actor=actor, note=note)
    return target


def _assert_actor_rules(
    target: HitlReviewState,
    *,
    actor: str | None,
    note: str | None,
) -> None:
    actor_norm = (actor or "").strip()
    note_norm = (note or "").strip()
    expert_decisions = {"accepted", "rejected", "edited", "waived"}
    if target in expert_decisions and not actor_norm:
        raise HitlTransitionError(f"{target} requires a non-empty actor")
    if target in {"rejected", "waived"} and not note_norm:
        raise HitlTransitionError(f"{target} requires a non-empty reason/note")
    if target == "edited" and not note_norm:
        raise HitlTransitionError("edited requires a non-empty note/diff description")
    if target in expert_decisions and actor_norm.lower() == "system":
        raise HitlTransitionError(
            f"{target} cannot be recorded as a system event; expert actor required"
        )


__all__ = [
    "HITL_REVIEW_STATES",
    "HitlReviewState",
    "HitlTransitionError",
    "assert_hitl_transition",
    "latest_hitl_state",
    "normalize_hitl_state",
]
