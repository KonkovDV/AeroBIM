"""Pair a title-block caption with the value cell beneath it.

GOST title blocks print the field name in the top of the cell and the value
below it. A caption that merely shares a baseline with a number is not this
pattern. The pair is a reading of the stamp. It does not write
``summary.passed`` and it is not a measurement against a rule.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.models import (
    DrawingAnnotation,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.stamp_dual_read import normalize_stamp_text

# Field name as printed, after ``normalize_stamp_text``, and the stable code
# stored on the annotation. Closed list: an unknown line is not a caption.
_CAPTION_CODES: dict[str, str] = {
    "лист": "sheet",
    "стадия": "stage",
    "изм.": "change",
    "изм": "change",
    "разраб.": "author",
    "разраб": "author",
    "н.контр.": "checker",
    "н.контр": "checker",
    "шифр": "cipher",
}

# From the bottom of the caption to the top of the value, in page points.
_MAX_GAP_PT = 18.0
# A value may start this far inside the caption box when the two lines touch.
_TOUCH_SLACK_PT = 1.0
# Share of the narrower box that must overlap on x. A side-by-side neighbour
# does not qualify.
_MIN_X_OVERLAP = 0.5
# A package has one cipher and one stage. Sheet numbers, authors and change
# marks are allowed to differ from sheet to sheet.
_PACKAGE_STABLE_CODES = frozenset({"cipher", "stage"})
STAMP_CAPTION_SOURCE = "stamp-caption-above"
STAMP_FIELD_DISAGREE = "AEROBIM-STAMP-FIELD-DISAGREE"


@dataclass(frozen=True, slots=True)
class PlacedLine:
    """One text line. ``y`` is the top edge in a top-left page frame."""

    text: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class CaptionAboveValue:
    """One caption and the single value cell beneath it."""

    code: str
    caption: str
    value: str
    x: float
    y: float
    width: float
    height: float


def disagreeing_package_stamp_fields(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn when a package-stable stamp field has two values.

    Cipher and stage are read from the caption above the cell. Sheet numbers
    are not compared. The rule is unsigned, so the finding is a warning: it
    is visible and it does not by itself fail the pack.
    """

    grouped: dict[str, list[DrawingAnnotation]] = {}
    for annotation in annotations:
        if (annotation.source or "") != STAMP_CAPTION_SOURCE:
            continue
        code = (annotation.measure_name or "").strip().casefold()
        if code not in _PACKAGE_STABLE_CODES:
            continue
        if not (annotation.observed_value or "").strip():
            continue
        grouped.setdefault(code, []).append(annotation)

    issues: list[ValidationIssue] = []
    for code in sorted(grouped):
        by_norm: dict[str, DrawingAnnotation] = {}
        for annotation in grouped[code]:
            key = normalize_stamp_text(annotation.observed_value or "")
            by_norm.setdefault(key, annotation)
        if len(by_norm) < 2:
            continue
        chosen = [by_norm[key] for key in sorted(by_norm)]
        shown = [(item.observed_value or "").strip() for item in chosen]
        refs = tuple(f"stamp:{code}@{item.sheet_id}#{item.annotation_id}" for item in chosen)
        issues.append(
            ValidationIssue(
                rule_id=STAMP_FIELD_DISAGREE,
                severity=Severity.WARNING,
                message=(
                    f"Stamp field {code} differs across sheets: {', '.join(shown)}. "
                    "Unsigned title-block reading; it does not by itself fail the pack."
                ),
                category=FindingCategory.CROSS_DOCUMENT,
                property_name=code,
                expected_value=shown[0],
                observed_value=shown[1],
                problem_zone=chosen[1].problem_zone,
                source_id=chosen[1].sheet_id,
                evidence_modality="drawing",
                evidence_refs=refs,
                origin="deterministic",
                answer_nature="deterministic",
                gate_class="quality",
            )
        )
    return issues


def writes_summary_passed() -> bool:
    """Stamp geometry does not own the package verdict."""

    return False


def pair_captions_above_values(
    lines: tuple[PlacedLine, ...] | list[PlacedLine],
) -> tuple[CaptionAboveValue, ...]:
    """Return pairs where exactly one value sits under exactly one caption.

    Two candidate values, or two captions claiming one value, yield no pair.
    Guessing would put the wrong cell into the report.
    """

    placed = [
        line for line in lines if line.width > 0.0 and line.height > 0.0 and line.text.strip()
    ]
    claims: list[tuple[int, int]] = []
    for caption_index, caption in enumerate(placed):
        if _caption_code(caption.text) is None:
            continue
        for value_index, value in enumerate(placed):
            if value_index == caption_index:
                continue
            if _caption_code(value.text) is not None:
                continue
            if _value_is_under(caption, value):
                claims.append((caption_index, value_index))

    by_caption: dict[int, list[int]] = {}
    by_value: dict[int, list[int]] = {}
    for caption_index, value_index in claims:
        by_caption.setdefault(caption_index, []).append(value_index)
        by_value.setdefault(value_index, []).append(caption_index)

    pairs: list[CaptionAboveValue] = []
    for caption_index, value_indexes in by_caption.items():
        if len(value_indexes) != 1:
            continue
        value_index = value_indexes[0]
        if len(by_value.get(value_index, ())) != 1:
            continue
        caption = placed[caption_index]
        value = placed[value_index]
        code = _caption_code(caption.text)
        if code is None:
            continue
        pairs.append(
            CaptionAboveValue(
                code=code,
                caption=normalize_stamp_text(caption.text),
                value=value.text.strip(),
                x=value.x,
                y=value.y,
                width=value.width,
                height=value.height,
            )
        )
    pairs.sort(key=lambda item: (item.y, item.x, item.code))
    return tuple(pairs)


def _caption_code(text: str) -> str | None:
    return _CAPTION_CODES.get(normalize_stamp_text(text))


def _value_is_under(caption: PlacedLine, value: PlacedLine) -> bool:
    gap = value.y - (caption.y + caption.height)
    if gap < -_TOUCH_SLACK_PT or gap > _MAX_GAP_PT:
        return False
    overlap = _x_overlap(caption, value)
    narrower = min(caption.width, value.width)
    return overlap >= _MIN_X_OVERLAP * narrower


def _x_overlap(left: PlacedLine, right: PlacedLine) -> float:
    start = max(left.x, right.x)
    end = min(left.x + left.width, right.x + right.width)
    return max(0.0, end - start)


__all__ = [
    "CaptionAboveValue",
    "PlacedLine",
    "STAMP_CAPTION_SOURCE",
    "STAMP_FIELD_DISAGREE",
    "disagreeing_package_stamp_fields",
    "pair_captions_above_values",
    "writes_summary_passed",
]
