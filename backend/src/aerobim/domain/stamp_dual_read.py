"""K2A-P1-04: dual-read of a PDF title-block (stamp) field -> ABSTAIN on disagreement.

Pure decision logic for the drawing/PDF layer only. IFC/IDS checks are
deterministic and never pass through here. OCR/VLM never issues a verdict:
the only positive outcome is ``AGREED`` (vector text == OCR text after
normalisation); everything else is ``ABSTAIN`` or ``NOT_VERIFIED`` and must
be routed to HITL, never to an OK capability.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class DualReadStatus(StrEnum):
    AGREED = "AGREED"
    ABSTAIN = "ABSTAIN"
    NOT_VERIFIED = "NOT_VERIFIED"


class DualReadReason(StrEnum):
    MATCH = "match"
    NOT_FOUND = "not_found"
    UNREADABLE = "unreadable"
    DISAGREEMENT = "vector_ocr_disagreement"


@dataclass(frozen=True, slots=True)
class DualReadResult:
    field: str
    status: DualReadStatus
    reason: DualReadReason
    value: str | None
    vector_text: str | None
    ocr_text: str | None

    @property
    def requires_hitl(self) -> bool:
        return self.status is not DualReadStatus.AGREED


_WS = re.compile(r"\s+")


def normalize_stamp_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).replace("ё", "е").replace("Ё", "Е")
    return _WS.sub(" ", t).strip().casefold()


def dual_read_stamp_field(
    field: str,
    vector_text: str | None,
    ocr_text: str | None,
    *,
    ocr_confidence: float | None = None,
    min_ocr_confidence: float = 0.5,
) -> DualReadResult:
    """Combine vector-layer and OCR reads; any doubt => not AGREED."""

    v = normalize_stamp_text(vector_text) if vector_text else ""
    o = normalize_stamp_text(ocr_text) if ocr_text else ""
    low_conf = ocr_confidence is not None and ocr_confidence < min_ocr_confidence

    def res(s: DualReadStatus, r: DualReadReason, val: str | None = None) -> DualReadResult:
        return DualReadResult(field, s, r, val, vector_text, ocr_text)

    if not v and not o:
        return res(DualReadStatus.NOT_VERIFIED, DualReadReason.NOT_FOUND)
    if not v or not o or low_conf:
        return res(DualReadStatus.ABSTAIN, DualReadReason.UNREADABLE)
    if v != o:
        return res(DualReadStatus.ABSTAIN, DualReadReason.DISAGREEMENT)
    return res(
        DualReadStatus.AGREED, DualReadReason.MATCH, vector_text.strip() if vector_text else None
    )
