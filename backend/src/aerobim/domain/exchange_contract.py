"""Versioned exchange records for a finding and a human decision.

The required keys are the contract. Dropping one is a breaking change.
A record never carries ``summary.passed``. An empty evidence list is not
a finding. This is not a CDE import and not an acceptance profile.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from aerobim.domain.finding_lifecycle import ReviewAction
from aerobim.domain.models import ValidationIssue

EXCHANGE_SCHEMA_VERSION: Final = "1.0.0"

FINDING_REQUIRED: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "finding_id",
        "rule_id",
        "severity",
        "origin",
        "evidence_refs",
        "message",
        "writes_summary_passed",
    }
)

DECISION_REQUIRED: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "finding_id",
        "action",
        "actor",
        "note",
        "writes_summary_passed",
    }
)

_REASON_REQUIRED: Final[frozenset[ReviewAction]] = frozenset(
    {
        ReviewAction.REJECT,
        ReviewAction.FALSE_POSITIVE,
        ReviewAction.NEEDS_CLARIFICATION,
    }
)


def finding_exchange(issue: ValidationIssue) -> dict[str, object]:
    """Project one issue. Refuses a record that cannot be cited."""

    finding_id = (issue.finding_id or "").strip()
    if not finding_id:
        raise ValueError("finding_id is required")
    refs = tuple(ref.strip() for ref in issue.evidence_refs if ref.strip())
    if not refs:
        raise ValueError("evidence_refs is required")
    origin = issue.origin or "deterministic"
    if origin not in {"deterministic", "advisory"}:
        raise ValueError(f"origin {origin!r} is not an exchange origin")
    record: dict[str, object] = {
        "schema_version": EXCHANGE_SCHEMA_VERSION,
        "finding_id": finding_id,
        "rule_id": issue.rule_id,
        "severity": issue.severity.value,
        "origin": origin,
        "evidence_refs": list(refs),
        "message": issue.message,
        "writes_summary_passed": False,
    }
    missing = contract_gaps(record, FINDING_REQUIRED)
    if missing:
        raise ValueError(f"finding exchange missing {sorted(missing)}")
    return record


def decision_exchange(
    *,
    finding_id: str,
    action: ReviewAction,
    actor: str,
    note: str | None = None,
) -> dict[str, object]:
    """Project one human decision. A refusal needs a note. It does not pass the pack."""

    fid = finding_id.strip()
    who = actor.strip()
    text = (note or "").strip()
    if not fid:
        raise ValueError("finding_id is required")
    if not who:
        raise ValueError("actor is required")
    if action in _REASON_REQUIRED and not text:
        raise ValueError("note is required for this action")
    record: dict[str, object] = {
        "schema_version": EXCHANGE_SCHEMA_VERSION,
        "finding_id": fid,
        "action": action.value,
        "actor": who,
        "note": text,
        "writes_summary_passed": False,
    }
    missing = contract_gaps(record, DECISION_REQUIRED)
    if missing:
        raise ValueError(f"decision exchange missing {sorted(missing)}")
    return record


def contract_gaps(record: Mapping[str, object], required: frozenset[str]) -> frozenset[str]:
    """Keys the contract demands and the record does not carry."""

    return required - set(record)
