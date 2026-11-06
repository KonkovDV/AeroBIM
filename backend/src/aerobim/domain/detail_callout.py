"""A cited detail that no sheet title names.

The citation is not proof the detail is absent from a signed set. Neither
side is the required detail. This does not write ``summary.passed``.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from aerobim.domain.models import (
    DrawingAnnotation,
    FindingCategory,
    Severity,
    ValidationIssue,
)

DETAIL_CALLOUT_SOURCE = "detail-callout"
DETAIL_TITLE_SOURCE = "detail-title"
DETAIL_CALLOUT_MISSING = "AEROBIM-DETAIL-CALLOUT-MISSING"

_CALLOUT = re.compile(r"(?i)(?:см\.?\s*узел|see\s+detail|see\s+node)\s*№?\s*(?P<id>\d{1,3})\b")
_TITLE = re.compile(r"(?i)^(?:узел|detail|node)\s*№?\s*(?P<id>\d{1,3})$")


def detail_title_id(text: str) -> str | None:
    """A line that is only the detail name. A sentence is not a title."""

    match = _TITLE.fullmatch((text or "").strip())
    if match is None:
        return None
    return _canonical_id(match.group("id"))


def detail_callout_id(text: str) -> str | None:
    """A citation of a detail. A title line is not a citation."""

    if detail_title_id(text) is not None:
        return None
    match = _CALLOUT.search(text or "")
    if match is None:
        return None
    return _canonical_id(match.group("id"))


def missing_detail_callouts(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn once per cited detail that no sheet title names.

    Leading zeros do not make a second detail. The warning does not by
    itself fail the pack.
    """

    titled: set[str] = set()
    callouts: dict[str, list[DrawingAnnotation]] = {}
    for annotation in annotations:
        source = annotation.source or ""
        detail_id = _canonical_id(annotation.observed_value or "")
        if detail_id is None:
            continue
        if source == DETAIL_TITLE_SOURCE:
            titled.add(detail_id)
        elif source == DETAIL_CALLOUT_SOURCE:
            callouts.setdefault(detail_id, []).append(annotation)

    issues: list[ValidationIssue] = []
    for detail_id in sorted(callouts, key=int):
        if detail_id in titled:
            continue
        ordered = sorted(
            callouts[detail_id],
            key=lambda item: (item.sheet_id, item.annotation_id),
        )
        sheet_ids: list[str] = []
        for item in ordered:
            if item.sheet_id not in sheet_ids:
                sheet_ids.append(item.sheet_id)
        refs = tuple(f"detail:{detail_id}@{item.sheet_id}#{item.annotation_id}" for item in ordered)
        issues.append(
            ValidationIssue(
                rule_id=DETAIL_CALLOUT_MISSING,
                severity=Severity.WARNING,
                message=(
                    f"Detail {detail_id} is cited on {', '.join(sheet_ids)} and no sheet "
                    "title names it. The citation is not proof the detail is absent "
                    "from a signed set."
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                property_name="detail",
                expected_value=None,
                observed_value=detail_id,
                problem_zone=ordered[-1].problem_zone,
                source_id=ordered[-1].sheet_id,
                evidence_modality="drawing",
                evidence_refs=refs,
                origin="deterministic",
                answer_nature="deterministic",
                gate_class="quality",
            )
        )
    return issues


def writes_summary_passed() -> bool:
    return False


def _canonical_id(raw: str) -> str | None:
    text = (raw or "").strip()
    if not text.isdigit():
        return None
    return str(int(text))


__all__ = [
    "DETAIL_CALLOUT_MISSING",
    "DETAIL_CALLOUT_SOURCE",
    "DETAIL_TITLE_SOURCE",
    "detail_callout_id",
    "detail_title_id",
    "missing_detail_callouts",
    "writes_summary_passed",
]
