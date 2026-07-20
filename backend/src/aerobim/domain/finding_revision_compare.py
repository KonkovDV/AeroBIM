"""Compare findings across package revisions (pilot engineering — not customer packs).

Match keys prefer stable identity over free-text messages:
``finding_id`` → ``rule_id + element_guid`` → ``rule_id + source_id + target_ref``.
Message text alone never establishes a match.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from aerobim.domain.models import Severity, ValidationIssue

FindingLike = ValidationIssue | Mapping[str, Any]


class FindingRevisionStatus(StrEnum):
    NEW = "new"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    RESOLVED = "resolved"
    REGRESSED = "regressed"
    CANNOT_MATCH = "cannot_match"


@dataclass(frozen=True)
class FindingRevisionDelta:
    status: FindingRevisionStatus
    match_key: str
    match_basis: str
    previous: dict[str, Any] | None
    current: dict[str, Any] | None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


_SEVERITY_RANK = {
    "info": 0,
    "warning": 1,
    "error": 2,
    Severity.INFO.value: 0,
    Severity.WARNING.value: 1,
    Severity.ERROR.value: 2,
}


def compare_findings_across_revisions(
    previous: Sequence[FindingLike],
    current: Sequence[FindingLike],
) -> list[FindingRevisionDelta]:
    """Diff two finding sets from successive revisions.

    Does **not** claim customer revision packs — fixture/engineering only until
    signed customer evidence exists.
    """

    prev_rows = [_normalize_finding(item, index=i) for i, item in enumerate(previous)]
    curr_rows = [_normalize_finding(item, index=i) for i, item in enumerate(current)]

    prev_by_key = _index_by_match_key(prev_rows)
    curr_by_key = _index_by_match_key(curr_rows)

    ambiguous_keys = {
        key
        for key in set(prev_by_key) | set(curr_by_key)
        if len(prev_by_key.get(key, ())) > 1 or len(curr_by_key.get(key, ())) > 1
    }

    deltas: list[FindingRevisionDelta] = []
    consumed_prev: set[int] = set()
    consumed_curr: set[int] = set()

    for key in sorted(set(prev_by_key) | set(curr_by_key)):
        if key in ambiguous_keys:
            for row in prev_by_key.get(key, ()):
                if row["index"] in consumed_prev:
                    continue
                consumed_prev.add(row["index"])
                deltas.append(
                    FindingRevisionDelta(
                        status=FindingRevisionStatus.CANNOT_MATCH,
                        match_key=key,
                        match_basis=row["match_basis"],
                        previous=row["snapshot"],
                        current=None,
                        notes="Ambiguous match key across revisions; not force-matched by message",
                    )
                )
            for row in curr_by_key.get(key, ()):
                if row["index"] in consumed_curr:
                    continue
                consumed_curr.add(row["index"])
                deltas.append(
                    FindingRevisionDelta(
                        status=FindingRevisionStatus.CANNOT_MATCH,
                        match_key=key,
                        match_basis=row["match_basis"],
                        previous=None,
                        current=row["snapshot"],
                        notes="Ambiguous match key across revisions; not force-matched by message",
                    )
                )
            continue

        prev_list = prev_by_key.get(key, ())
        curr_list = curr_by_key.get(key, ())
        if prev_list and curr_list:
            prev_row = prev_list[0]
            curr_row = curr_list[0]
            consumed_prev.add(prev_row["index"])
            consumed_curr.add(curr_row["index"])
            deltas.append(
                _paired_delta(
                    match_key=key,
                    previous=prev_row,
                    current=curr_row,
                )
            )
        elif curr_list and not prev_list:
            curr_row = curr_list[0]
            consumed_curr.add(curr_row["index"])
            deltas.append(
                FindingRevisionDelta(
                    status=FindingRevisionStatus.NEW,
                    match_key=key,
                    match_basis=curr_row["match_basis"],
                    previous=None,
                    current=curr_row["snapshot"],
                )
            )
        elif prev_list and not curr_list:
            prev_row = prev_list[0]
            consumed_prev.add(prev_row["index"])
            deltas.append(
                FindingRevisionDelta(
                    status=FindingRevisionStatus.RESOLVED,
                    match_key=key,
                    match_basis=prev_row["match_basis"],
                    previous=prev_row["snapshot"],
                    current=None,
                )
            )

    deltas.sort(key=lambda item: (item.status.value, item.match_key))
    return deltas


def export_finding_revision_delta_document(
    *,
    previous_revision: str | None,
    current_revision: str | None,
    deltas: Sequence[FindingRevisionDelta],
) -> dict[str, Any]:
    """JSON-ready export — engineering harness only, not customer pack evidence."""

    counts: dict[str, int] = {status.value: 0 for status in FindingRevisionStatus}
    for delta in deltas:
        counts[delta.status.value] += 1
    return {
        "artifact_type": "aerobim_finding_revision_delta",
        "schema_version": "1.0.0",
        "previous_revision": previous_revision,
        "current_revision": current_revision,
        "claim_boundary": (
            "Engineering revision compare only — not a customer revision pack claim"
        ),
        "counts": counts,
        "deltas": [delta.as_dict() for delta in deltas],
    }


def _paired_delta(
    *,
    match_key: str,
    previous: dict[str, Any],
    current: dict[str, Any],
) -> FindingRevisionDelta:
    prev_fp = previous["fingerprint"]
    curr_fp = current["fingerprint"]
    if prev_fp == curr_fp:
        status = FindingRevisionStatus.UNCHANGED
        notes = ""
    elif _severity_rank(current["snapshot"].get("severity")) > _severity_rank(
        previous["snapshot"].get("severity")
    ):
        status = FindingRevisionStatus.REGRESSED
        notes = "Severity increased across revisions"
    else:
        status = FindingRevisionStatus.CHANGED
        notes = "Matched identity with changed severity or observed/expected values"
    return FindingRevisionDelta(
        status=status,
        match_key=match_key,
        match_basis=current["match_basis"],
        previous=previous["snapshot"],
        current=current["snapshot"],
        notes=notes,
    )


def _index_by_match_key(
    rows: Sequence[dict[str, Any]],
) -> dict[str, tuple[dict[str, Any], ...]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(row["match_key"], []).append(row)
    return {key: tuple(values) for key, values in buckets.items()}


def _normalize_finding(item: FindingLike, *, index: int) -> dict[str, Any]:
    if isinstance(item, ValidationIssue):
        finding_id = (item.finding_id or "").strip() or None
        rule_id = (item.rule_id or "").strip()
        element_guid = (item.element_guid or "").strip() or None
        source_id = (item.source_id or "").strip() or None
        target_ref = (item.target_ref or "").strip() or None
        severity = item.severity.value if item.severity is not None else None
        expected = item.expected_value
        observed = item.observed_value
        category = item.category.value if item.category is not None else None
    elif isinstance(item, Mapping):
        finding_id = _optional_str(item.get("finding_id"))
        rule_id = _optional_str(item.get("rule_id")) or ""
        element_guid = _optional_str(item.get("element_guid"))
        source_id = _optional_str(item.get("source_id")) or _optional_str(item.get("document_id"))
        target_ref = _optional_str(item.get("target_ref"))
        severity = _optional_str(item.get("severity"))
        expected = item.get("expected_value")
        observed = item.get("observed_value")
        category = _optional_str(item.get("category"))
    else:
        raise TypeError(f"Unsupported finding type: {type(item)!r}")

    if not rule_id and not finding_id:
        raise ValueError("Finding requires rule_id or finding_id for revision compare")

    if finding_id:
        match_key = f"finding_id:{finding_id}"
        match_basis = "finding_id"
    elif element_guid:
        match_key = f"rule+guid:{rule_id}|{element_guid}"
        match_basis = "rule_id+element_guid"
    elif source_id or target_ref:
        match_key = f"rule+doc:{rule_id}|{source_id or ''}|{target_ref or ''}"
        match_basis = "rule_id+document_identity"
    else:
        # Last resort: rule only — still never message text.
        match_key = f"rule_only:{rule_id}"
        match_basis = "rule_id"

    snapshot = {
        "finding_id": finding_id,
        "rule_id": rule_id,
        "element_guid": element_guid,
        "source_id": source_id,
        "target_ref": target_ref,
        "severity": severity,
        "expected_value": expected,
        "observed_value": observed,
        "category": category,
    }
    fingerprint = (
        severity or "",
        str(expected or ""),
        str(observed or ""),
        category or "",
    )
    return {
        "index": index,
        "match_key": match_key,
        "match_basis": match_basis,
        "snapshot": snapshot,
        "fingerprint": fingerprint,
    }


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    return stripped or None


def _severity_rank(value: object) -> int:
    if value is None:
        return -1
    if isinstance(value, Severity):
        return _SEVERITY_RANK.get(value.value, -1)
    return _SEVERITY_RANK.get(str(value).strip().lower(), -1)


__all__ = [
    "FindingRevisionDelta",
    "FindingRevisionStatus",
    "compare_findings_across_revisions",
    "export_finding_revision_delta_document",
]
