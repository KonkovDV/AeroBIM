"""Two sheets may print different readings for one measure.

A reading may be a number or a short execution token. Neither reading is
the required value. The warning is a drawing record. It does not write
``summary.passed`` and it is not a calculation.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from aerobim.domain.detail_callout import DETAIL_CALLOUT_SOURCE, DETAIL_TITLE_SOURCE
from aerobim.domain.models import (
    DrawingAnnotation,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.stamp_caption_above import (
    SHEET_BODY_TITLE_SOURCE,
    STAMP_CAPTION_SOURCE,
    stamp_comparison_key,
)

DRAWING_MEASURE_DISAGREE = "AEROBIM-DRAWING-MEASURE-DISAGREE"
_EXECUTION_MEASURE = "execution"
_NOT_A_MEASURE = frozenset(
    {
        STAMP_CAPTION_SOURCE,
        SHEET_BODY_TITLE_SOURCE,
        DETAIL_CALLOUT_SOURCE,
        DETAIL_TITLE_SOURCE,
    }
)
_EXECUTION_TOKEN = re.compile(r"^[A-Za-zА-Яа-яЁё0-9]{1,4}$")


def _number_key(value: str) -> str | None:
    text = (value or "").replace(",", ".").replace(" ", "").strip()
    if not text:
        return None
    try:
        quantized = format(Decimal(text), "f")
    except InvalidOperation:
        return None
    if "." in quantized:
        quantized = quantized.rstrip("0").rstrip(".")
    return quantized or None


def disagreeing_drawing_measures(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn when one measure has two numeric readings on different sheets.

    Stamp captions are not measures. A repeated reading on one sheet is quiet.
    """

    grouped: dict[tuple[str, str, str], list[DrawingAnnotation]] = {}
    for annotation in annotations:
        if (annotation.source or "") in _NOT_A_MEASURE:
            continue
        number = _number_key(annotation.observed_value or "")
        if number is None:
            continue
        target = (annotation.target_ref or "").strip()
        measure = (annotation.measure_name or "").strip()
        if not target or not measure:
            continue
        key = (target.casefold(), measure.casefold(), (annotation.unit or "").casefold())
        grouped.setdefault(key, []).append(annotation)

    issues: list[ValidationIssue] = []
    for key in sorted(grouped):
        by_number: dict[str, list[DrawingAnnotation]] = {}
        for annotation in grouped[key]:
            number = _number_key(annotation.observed_value or "")
            if number is None:
                continue
            by_number.setdefault(number, []).append(annotation)
        if len(by_number) < 2:
            continue
        target, measure, unit = key
        groups = [
            sorted(by_number[number], key=lambda item: (item.sheet_id, item.annotation_id))
            for number in sorted(by_number, key=lambda item: (Decimal(item), item))
        ]
        issue = _readings_issue(target=target, measure=measure, unit=unit or None, groups=groups)
        if issue is not None:
            issues.append(issue)
    issues.extend(_execution_token_issues(annotations))
    return issues


def _execution_token_issues(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Two short execution tokens for one target on two sheets.

    A title is not an execution. Neither token is the required value.
    """

    grouped: dict[str, list[DrawingAnnotation]] = {}
    for annotation in annotations:
        source = annotation.source or ""
        if source in _NOT_A_MEASURE:
            continue
        if (annotation.measure_name or "").strip().casefold() != _EXECUTION_MEASURE:
            continue
        token = (annotation.observed_value or "").strip()
        if _EXECUTION_TOKEN.fullmatch(token) is None:
            continue
        target = (annotation.target_ref or "").strip()
        if not target:
            continue
        grouped.setdefault(target.casefold(), []).append(annotation)

    issues: list[ValidationIssue] = []
    for target in sorted(grouped):
        by_token: dict[str, list[DrawingAnnotation]] = {}
        for annotation in grouped[target]:
            key = stamp_comparison_key(annotation.observed_value or "")
            by_token.setdefault(key, []).append(annotation)
        if len(by_token) < 2:
            continue
        groups = [
            sorted(by_token[key], key=lambda item: (item.sheet_id, item.annotation_id))
            for key in sorted(by_token)
        ]
        issue = _readings_issue(
            target=target,
            measure=_EXECUTION_MEASURE,
            unit=None,
            groups=groups,
        )
        if issue is not None:
            issues.append(issue)
    return issues


def _readings_issue(
    *,
    target: str,
    measure: str,
    unit: str | None,
    groups: list[list[DrawingAnnotation]],
) -> ValidationIssue | None:
    """One warning for two readings. One sheet, however many rows, stays quiet."""

    shown: list[str] = []
    flat: list[DrawingAnnotation] = []
    sheets: list[str] = []
    for ordered in groups:
        if not ordered:
            continue
        sheet_ids: list[str] = []
        for item in ordered:
            if item.sheet_id not in sheet_ids:
                sheet_ids.append(item.sheet_id)
            if item.sheet_id not in sheets:
                sheets.append(item.sheet_id)
        printed = (ordered[0].observed_value or "").strip()
        shown.append(f"{printed} ({', '.join(sheet_ids)})")
        flat.extend(ordered)
    if len(sheets) < 2 or not flat:
        return None
    return ValidationIssue(
        rule_id=DRAWING_MEASURE_DISAGREE,
        severity=Severity.WARNING,
        message=(
            f"Measure {measure} of {target} differs across sheets: "
            f"{'; '.join(shown)}. Neither reading is the required value."
        ),
        category=FindingCategory.DRAWING_VALIDATION,
        property_name=measure,
        expected_value=None,
        observed_value="; ".join(shown),
        unit=unit,
        problem_zone=flat[-1].problem_zone,
        source_id=flat[-1].sheet_id,
        evidence_modality="drawing",
        evidence_refs=tuple(
            f"measure:{measure}@{item.sheet_id}#{item.annotation_id}" for item in flat
        ),
        origin="deterministic",
        answer_nature="deterministic",
        gate_class="quality",
    )


def writes_summary_passed() -> bool:
    return False


__all__ = [
    "DRAWING_MEASURE_DISAGREE",
    "disagreeing_drawing_measures",
    "writes_summary_passed",
]
