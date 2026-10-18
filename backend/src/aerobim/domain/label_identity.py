"""Identity of sheet marks: homoglyphs and short system-mark lists.

Cyrillic and Latin lookalikes in a steel grade are one token (``С345`` and
``C345``). Latin ``I`` is not folded: Roman numerals must stay distinct.
A ventilation schedule writes ``В2.7,8,9`` or ``В2.4-В2.6`` for several
risers; a grille size such as ``П300*300`` is not a mark list.
This is label identity on the pack seam, not a system-clash verdict.
"""

from __future__ import annotations

import re

# Lookalikes only. Latin I is omitted on purpose (Roman numerals).
_HOMOGLYPH_FOLD = str.maketrans(
    {
        "А": "A",
        "а": "a",
        "В": "B",
        "в": "b",
        "Е": "E",
        "е": "e",
        "К": "K",
        "к": "k",
        "М": "M",
        "м": "m",
        "Н": "H",
        "н": "h",
        "О": "O",
        "о": "o",
        "Р": "P",
        "р": "p",
        "С": "C",
        "с": "c",
        "Т": "T",
        "т": "t",
        "У": "Y",
        "у": "y",
        "Х": "X",
        "х": "x",
    }
)

# System-mark heads are stored in Cyrillic. Latin lookalikes fold that way
# only inside the expander, so ``B2.1`` and ``В2.1`` are one riser.
_MARK_TO_CYRILLIC = str.maketrans("ABCEHKMOPTXY", "АВСЕНКМОРТХУ")
_HEAD = r"(ПЕ|ВЕ|ПД|ДУ|П|В)"
_RANGE = re.compile(
    rf"^{_HEAD}(\d{{1,2}})\.(\d{{1,2}})\s*[-–—]\s*(?:{_HEAD}(\d{{1,2}})\.)?(\d{{1,2}})$"
)
_LIST = re.compile(rf"^{_HEAD}(\d{{1,2}})\.(\d{{1,2}}(?:\s*,\s*\d{{1,2}})+)$")
_ONE = re.compile(rf"^{_HEAD}(\d{{1,2}}(?:\.\d{{1,2}})?)?$")


def fold_homoglyphs(value: str) -> str:
    """Map Cyrillic lookalikes to Latin. Case of every other character stays."""

    return value.translate(_HOMOGLYPH_FOLD)


def labels_equivalent(left: str, right: str) -> bool:
    """True when two non-numeric labels differ only by lookalike letters."""

    return fold_homoglyphs(left.strip()) == fold_homoglyphs(right.strip())


def expand_system_marks(text: str) -> tuple[str, ...]:
    """Expand a mark list or a short range. Empty when the text is not only marks."""

    folded = text.strip().upper().translate(_MARK_TO_CYRILLIC)
    folded = re.sub(r"\s*([,–—-])\s*", r"\1", folded)
    if not folded:
        return ()
    marks: list[str] = []
    for word in folded.split():
        word_marks: list[str] = []
        for part in re.split(r"[/\\]", word.strip(" .:;,]|[()")):
            pieces = [piece for piece in part.split(",") if piece]
            if len(pieces) > 1 and all(_expand_token(piece) for piece in pieces):
                for piece in pieces:
                    word_marks.extend(_expand_token(piece))
                continue
            word_marks.extend(_expand_token(part))
        if not word_marks:
            return ()
        marks.extend(word_marks)
    return tuple(dict.fromkeys(marks))


def mark_sets_overlap(left: str, right: str) -> bool:
    """True when both sides are mark lists and they share one mark."""

    left_marks = expand_system_marks(left)
    right_marks = expand_system_marks(right)
    if not left_marks or not right_marks:
        return False
    return bool(set(left_marks) & set(right_marks))


def _expand_token(part: str) -> tuple[str, ...]:
    if not part or "*" in part:
        return ()
    ranged = _RANGE.fullmatch(part)
    if ranged is not None:
        prefix, system, start, other_prefix, other_system, end = ranged.groups()
        if other_prefix is not None and (other_prefix != prefix or other_system != system):
            return ()
        left, right = int(start), int(end)
        if 0 < right - left <= 12:
            return tuple(f"{prefix}{system}.{index}" for index in range(left, right + 1))
        return ()
    listed = _LIST.fullmatch(part)
    if listed is not None:
        prefix, system, tail = listed.groups()
        return tuple(f"{prefix}{system}.{int(piece)}" for piece in re.split(r"\s*,\s*", tail))
    single = _ONE.fullmatch(part)
    if single is None:
        return ()
    prefix, number = single.groups()
    if number is None:
        return (prefix,) if prefix in {"ВЕ", "ПЕ"} else ()
    if number.startswith("0") and "." not in number:
        return ()
    return (f"{prefix}{number}",)
