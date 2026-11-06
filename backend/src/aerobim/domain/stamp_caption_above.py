"""Pair a title-block caption with the value cell beneath it.

GOST title blocks print the field name in the top of the cell and the value
below it. A caption that merely shares a baseline with a number is not this
pattern. The pair is a reading of the stamp. It does not write
``summary.passed`` and it is not a measurement against a rule.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from aerobim.domain.label_identity import fold_homoglyphs
from aerobim.domain.models import (
    DrawingAnnotation,
    FindingCategory,
    Severity,
    ValidationIssue,
)
from aerobim.domain.paired_dimension import is_paired_dimension
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
    "наименование": "name",
    "название": "name",
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
SHEET_BODY_TITLE_SOURCE = "sheet-body-title"
STAMP_FIELD_DISAGREE = "AEROBIM-STAMP-FIELD-DISAGREE"
STAMP_SHEET_COLLISION = "AEROBIM-STAMP-SHEET-COLLIDE"
STAMP_BODY_TITLE_DISAGREE = "AEROBIM-STAMP-BODY-TITLE"
STAMP_REVISION_UNMARKED = "AEROBIM-STAMP-REVISION-UNMARKED"
# Two body lines this close in height are one tie. A tie with different
# text is not a title: guessing would name the wrong line.
_HEIGHT_TIE_PT = 0.5
_MAX_TITLE_CHARS = 48
_TITLE_LETTER = re.compile(r"[A-Za-zА-Яа-яЁё]")
# A measure line is not the sheet title. The tallest line on a fixture
# sheet is often the dimension itself.
_MEASURE_LINE = re.compile(
    r"(?i)(?:thickness|width|height|length|area|толщина|ширина|высота|длина|"
    r"площадь|исполнение|execution|шт\.?|pcs|pc)\b"
)
# Visible title block: bottom-right 190 mm by 70 mm. A word in the body of
# the sheet is not the package cipher.
_MM_TO_PT = 72.0 / 25.4
TITLE_BLOCK_WIDTH_PT = 190.0 * _MM_TO_PT
TITLE_BLOCK_HEIGHT_PT = 70.0 * _MM_TO_PT
# A GOST or SNiP name, with or without a number glued on, is not a cipher.
# A roman clause (``СНиП II-23``) is not a cipher. A dotted SP clause
# (``СП 63.13330``) is not a cipher. A short code ``СП-1`` is.
# Hyphen, non-breaking hyphen, figure dash, en dash, em dash, minus.
_DASH_FOLD = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u00ad": "",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
    }
)
_DASH_SPACE = re.compile(r"\s*-\s*")
_STANDARD_CITATION = re.compile(
    r"(?i)(?:"
    r"(?:^|[\s№])(?:гост|gost|снип|snip)(?:\s*р)?"
    r"(?:[\s.\-]*\d|[\s.\-]+[ivx]+(?![\s.\-]*[a-zа-яё])(?:[\s.\-]+\d+)*|$)"
    r"|"
    r"(?:^|[\s№])(?:сп|sp)[\s.\-]*\d+\.\d+"
    r")"
)


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

    Cipher and stage are read from the caption above the cell. Every sheet
    that carries a value is named, in sheet order, so two runs of one package
    write one warning. Sheet numbers are not compared. The rule is unsigned,
    so the finding is a drawing warning: it is visible, it is not filed as a
    cross-document contradiction, and it does not by itself fail the pack.
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
        by_norm: dict[str, list[DrawingAnnotation]] = {}
        for annotation in grouped[code]:
            key = stamp_comparison_key(annotation.observed_value or "")
            by_norm.setdefault(key, []).append(annotation)
        if len(by_norm) < 2:
            continue
        chosen = [by_norm[key] for key in sorted(by_norm)]
        shown: list[str] = []
        flat: list[DrawingAnnotation] = []
        for items in chosen:
            ordered = sorted(items, key=lambda item: (item.sheet_id, item.annotation_id))
            printed = (ordered[0].observed_value or "").strip()
            sheets = ", ".join(item.sheet_id for item in ordered)
            shown.append(f"{printed} ({sheets})")
            flat.extend(ordered)
        refs = tuple(f"stamp:{code}@{item.sheet_id}#{item.annotation_id}" for item in flat)
        issues.append(
            ValidationIssue(
                rule_id=STAMP_FIELD_DISAGREE,
                severity=Severity.WARNING,
                message=(
                    f"Stamp field {code} differs across sheets: {'; '.join(shown)}. "
                    "Unsigned title-block reading; it does not by itself fail the pack."
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                property_name=code,
                expected_value=None,
                observed_value="; ".join(shown),
                problem_zone=flat[-1].problem_zone,
                source_id=flat[-1].sheet_id,
                evidence_modality="drawing",
                evidence_refs=refs,
                origin="deterministic",
                answer_nature="deterministic",
                gate_class="quality",
            )
        )
    return issues


def colliding_stamp_sheet_numbers(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn when two different sheets print the same sheet number.

    Sheet numbers may differ. The same number on two sheets is a collision:
    a reference to that number no longer names one sheet. The check is
    unsigned and does not by itself fail the pack.
    """

    by_number: dict[str, list[DrawingAnnotation]] = {}
    for annotation in annotations:
        if (annotation.source or "") != STAMP_CAPTION_SOURCE:
            continue
        if (annotation.measure_name or "").strip().casefold() != "sheet":
            continue
        raw = (annotation.observed_value or "").strip()
        if not raw:
            continue
        key = stamp_comparison_key(raw)
        if key.isdigit():
            key = str(int(key))
        by_number.setdefault(key, []).append(annotation)

    issues: list[ValidationIssue] = []
    for key in sorted(by_number):
        ordered = sorted(
            by_number[key],
            key=lambda item: (item.sheet_id, item.annotation_id),
        )
        sheet_ids: list[str] = []
        for item in ordered:
            if item.sheet_id not in sheet_ids:
                sheet_ids.append(item.sheet_id)
        if len(sheet_ids) < 2:
            continue
        printed = (ordered[0].observed_value or "").strip()
        refs = tuple(f"stamp:sheet@{item.sheet_id}#{item.annotation_id}" for item in ordered)
        issues.append(
            ValidationIssue(
                rule_id=STAMP_SHEET_COLLISION,
                severity=Severity.WARNING,
                message=(
                    f"Sheet number {printed} is printed on {', '.join(sheet_ids)}. "
                    "Unsigned title-block reading; it does not by itself fail the pack."
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                property_name="sheet",
                expected_value=None,
                observed_value=f"{printed} ({', '.join(sheet_ids)})",
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


def unmarked_stamp_revisions(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn once when stamps were read and carry neither cipher nor change.

    A sheet number alone does not tell one revision from another. One cipher
    or one change number anywhere in the pack is enough to stay quiet. The
    check is unsigned and does not by itself fail the pack.
    """

    sheets: list[DrawingAnnotation] = []
    has_cipher = False
    has_change = False
    for annotation in annotations:
        if (annotation.source or "") != STAMP_CAPTION_SOURCE:
            continue
        code = (annotation.measure_name or "").strip().casefold()
        if not (annotation.observed_value or "").strip():
            continue
        if code == "sheet":
            sheets.append(annotation)
        elif code == "cipher":
            has_cipher = True
        elif code == "change":
            has_change = True
    if not sheets or has_cipher or has_change:
        return []
    ordered = sorted(sheets, key=lambda item: (item.sheet_id, item.annotation_id))
    sheet_ids: list[str] = []
    for item in ordered:
        if item.sheet_id not in sheet_ids:
            sheet_ids.append(item.sheet_id)
    refs = tuple(f"stamp:sheet@{item.sheet_id}#{item.annotation_id}" for item in ordered)
    return [
        ValidationIssue(
            rule_id=STAMP_REVISION_UNMARKED,
            severity=Severity.WARNING,
            message=(
                f"Stamps on {len(sheet_ids)} sheets have neither a cipher nor a change "
                "number, so revisions of this pack cannot be told apart. "
                "Unsigned title-block reading; it does not by itself fail the pack."
            ),
            category=FindingCategory.DRAWING_VALIDATION,
            property_name="revision",
            expected_value=None,
            observed_value=str(len(sheet_ids)),
            problem_zone=ordered[-1].problem_zone,
            source_id=ordered[-1].sheet_id,
            evidence_modality="drawing",
            evidence_refs=refs,
            origin="deterministic",
            answer_nature="deterministic",
            gate_class="quality",
        )
    ]


def stamp_comparison_key(value: str) -> str:
    """One token for lookalike letters and for dashes that differ only in shape.

    The displayed value stays as printed. Spaces around a dash do not make a
    second cipher.
    """

    folded = fold_homoglyphs(normalize_stamp_text(value)).translate(_DASH_FOLD)
    return _DASH_SPACE.sub("-", folded)


def line_center_in_title_block(
    line: PlacedLine,
    *,
    page_width: float,
    page_height: float,
) -> bool:
    """True when the line centre sits in the bottom-right title block.

    Coordinates are top-left. A page smaller than the block still keeps the
    corner that exists.
    """

    if page_width <= 0.0 or page_height <= 0.0:
        return False
    center_x = line.x + (line.width / 2.0)
    center_y = line.y + (line.height / 2.0)
    return center_x >= page_width - TITLE_BLOCK_WIDTH_PT and center_y >= (
        page_height - TITLE_BLOCK_HEIGHT_PT
    )


def select_body_title(
    lines: Sequence[PlacedLine],
    *,
    page_width: float,
    page_height: float,
) -> PlacedLine | None:
    """The single tallest short letter-line outside the title block.

    A sheet name in the stamp is not this line. Two equally tall lines with
    different text yield nothing: the title is then unknown.
    """

    if page_width <= 0.0 or page_height <= 0.0:
        return None
    candidates = [
        line
        for line in lines
        if line.width > 0.0
        and line.height > 0.0
        and line.text.strip()
        and not line_center_in_title_block(line, page_width=page_width, page_height=page_height)
        and _is_body_title_text(line.text)
    ]
    if not candidates:
        return None
    tallest = max(line.height for line in candidates)
    near = [line for line in candidates if tallest - line.height <= _HEIGHT_TIE_PT]
    keys = {stamp_comparison_key(line.text) for line in near}
    if len(keys) != 1:
        return None
    return min(near, key=lambda line: (line.y, line.x, line.text))


def disagreeing_stamp_and_body_titles(
    annotations: Sequence[DrawingAnnotation],
) -> list[ValidationIssue]:
    """Warn when the stamp name and the body title on one sheet differ.

    The sheet name is not package-stable. Neither reading is the required
    name. The warning does not by itself fail the pack.
    """

    by_sheet: dict[str, list[DrawingAnnotation]] = {}
    for annotation in annotations:
        by_sheet.setdefault(annotation.sheet_id, []).append(annotation)

    issues: list[ValidationIssue] = []
    for sheet_id in sorted(by_sheet):
        stamps = _name_readings(by_sheet[sheet_id], STAMP_CAPTION_SOURCE)
        bodies = _name_readings(by_sheet[sheet_id], SHEET_BODY_TITLE_SOURCE)
        if not stamps or not bodies:
            continue
        stamp_keys = {stamp_comparison_key(item.observed_value or "") for item in stamps}
        body_keys = {stamp_comparison_key(item.observed_value or "") for item in bodies}
        if len(stamp_keys) != 1 or len(body_keys) != 1 or stamp_keys == body_keys:
            continue
        stamp = sorted(stamps, key=lambda item: item.annotation_id)[0]
        body = sorted(bodies, key=lambda item: item.annotation_id)[0]
        stamp_text = (stamp.observed_value or "").strip()
        body_text = (body.observed_value or "").strip()
        issues.append(
            ValidationIssue(
                rule_id=STAMP_BODY_TITLE_DISAGREE,
                severity=Severity.WARNING,
                message=(
                    f"Sheet {sheet_id} stamp name {stamp_text} and body title {body_text} "
                    "differ. Neither reading is the required name."
                ),
                category=FindingCategory.DRAWING_VALIDATION,
                property_name="name",
                expected_value=None,
                observed_value=f"{stamp_text}; {body_text}",
                problem_zone=body.problem_zone or stamp.problem_zone,
                source_id=sheet_id,
                evidence_modality="drawing",
                evidence_refs=(
                    f"stamp:name@{sheet_id}#{stamp.annotation_id}",
                    f"body:name@{sheet_id}#{body.annotation_id}",
                ),
                origin="deterministic",
                answer_nature="deterministic",
                gate_class="quality",
            )
        )
    return issues


def _name_readings(
    annotations: Sequence[DrawingAnnotation],
    source: str,
) -> list[DrawingAnnotation]:
    return [
        item
        for item in annotations
        if (item.source or "") == source
        and (item.measure_name or "").strip().casefold() == "name"
        and (item.observed_value or "").strip()
    ]


def _is_body_title_text(text: str) -> bool:
    raw = text.strip()
    if not raw or len(raw) > _MAX_TITLE_CHARS:
        return False
    if _caption_code(raw) is not None:
        return False
    if value_is_standard_citation(raw):
        return False
    if is_paired_dimension(raw):
        return False
    if _MEASURE_LINE.search(raw) is not None:
        return False
    letters = len(_TITLE_LETTER.findall(raw))
    if letters < 2:
        return False
    digits = sum(character.isdigit() for character in raw)
    return digits <= letters


def value_is_standard_citation(value: str) -> bool:
    """A GOST or SP citation is not a package cipher."""

    return _STANDARD_CITATION.search(value or "") is not None


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
    "SHEET_BODY_TITLE_SOURCE",
    "STAMP_BODY_TITLE_DISAGREE",
    "STAMP_CAPTION_SOURCE",
    "STAMP_FIELD_DISAGREE",
    "STAMP_REVISION_UNMARKED",
    "STAMP_SHEET_COLLISION",
    "TITLE_BLOCK_HEIGHT_PT",
    "TITLE_BLOCK_WIDTH_PT",
    "disagreeing_package_stamp_fields",
    "disagreeing_stamp_and_body_titles",
    "line_center_in_title_block",
    "select_body_title",
    "unmarked_stamp_revisions",
    "colliding_stamp_sheet_numbers",
    "pair_captions_above_values",
    "stamp_comparison_key",
    "value_is_standard_citation",
    "writes_summary_passed",
]
