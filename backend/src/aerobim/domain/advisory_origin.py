"""Single decoder for advisory (non-deterministic) validation issues.

Used by the reproducibility hash and the IFC Acceptance Gate so AGENT- prefixes,
``origin=advisory``, and the compliance-agent source cannot drift apart.
"""

from __future__ import annotations

from typing import Any

_ADVISORY_ORIGIN = "advisory"
_AGENT_SOURCE_ID = "compliance-agent"
_AGENT_RULE_PREFIXES = ("AGENT-", "AEROBIM-AGENT-")


def _raw(issue: Any, name: str) -> Any:
    if isinstance(issue, dict):
        return issue.get(name)
    return getattr(issue, name, None)


def _as_text(raw: Any) -> str:
    if raw is None:
        return ""
    if hasattr(raw, "value"):
        return str(raw.value)
    return str(raw)


def is_advisory_issue(issue: Any) -> bool:
    """True when the issue must not bind a deterministic hash or sell-path blocking count."""

    origin = _as_text(_raw(issue, "origin")).strip().lower()
    if origin == _ADVISORY_ORIGIN:
        return True
    source_id = _as_text(_raw(issue, "source_id")).strip()
    if source_id == _AGENT_SOURCE_ID:
        return True
    rule_id = _as_text(_raw(issue, "rule_id"))
    return rule_id.startswith(_AGENT_RULE_PREFIXES)
