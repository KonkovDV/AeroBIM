"""Content-addressed drawing annotation IDs (``drawing-annotation-id-v2``).

Builtin ``hash()`` is randomized per process via ``PYTHONHASHSEED`` and must
not be used for annotation identity, revision compare, or dedup.
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata

ANNOTATION_ID_SCHEMA = "drawing-annotation-id-v2"
# PDF user-space points. 0.001 pt is far below stamp/explication separation.
COORD_DECIMALS = 3
_DISPLAY_DIGEST_CHARS = 16


def canonical_coord(value: float) -> float:
    """Round a bbox coordinate; map NaN/inf to 0 so JSON stays RFC-compliant."""

    number = float(value)
    if not math.isfinite(number):
        return 0.0
    return round(number, COORD_DECIMALS)


def canonical_observed_value(value: str) -> str:
    """Strip and unify decimal comma so ``150,0`` and ``150.0`` share identity."""

    return str(value).strip().replace(",", ".")


def canonical_unit(unit: str | None) -> str:
    """NFC-normalize unit text. ``м²`` and ``м2`` stay distinct (no NFKC)."""

    return unicodedata.normalize("NFC", (unit or "").strip().lower())


def drawing_annotation_canonical(
    *,
    sheet_id: str,
    page_number: int,
    target_ref: str,
    measure_name: str,
    observed_value: str,
    unit: str | None,
    x: float,
    y: float,
    width: float,
    height: float,
) -> dict[str, object]:
    return {
        "schema": ANNOTATION_ID_SCHEMA,
        "bbox": {
            "height": canonical_coord(height),
            "width": canonical_coord(width),
            "x": canonical_coord(x),
            "y": canonical_coord(y),
        },
        "measure_name": measure_name.strip().lower(),
        "observed_value": canonical_observed_value(observed_value),
        "page_number": int(page_number),
        "sheet_id": sheet_id,
        "target_ref": target_ref.strip().upper(),
        "unit": canonical_unit(unit),
    }


def drawing_annotation_digest(
    *,
    sheet_id: str,
    page_number: int,
    target_ref: str,
    measure_name: str,
    observed_value: str,
    unit: str | None,
    x: float,
    y: float,
    width: float,
    height: float,
) -> str:
    canonical = drawing_annotation_canonical(
        sheet_id=sheet_id,
        page_number=page_number,
        target_ref=target_ref,
        measure_name=measure_name,
        observed_value=observed_value,
        unit=unit,
        x=x,
        y=y,
        width=width,
        height=height,
    )
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def drawing_annotation_id(
    *,
    sheet_id: str,
    page_number: int,
    target_ref: str,
    measure_name: str,
    observed_value: str,
    unit: str | None,
    x: float,
    y: float,
    width: float,
    height: float,
) -> str:
    digest = drawing_annotation_digest(
        sheet_id=sheet_id,
        page_number=page_number,
        target_ref=target_ref,
        measure_name=measure_name,
        observed_value=observed_value,
        unit=unit,
        x=x,
        y=y,
        width=width,
        height=height,
    )
    return f"VIS-{int(page_number):03d}-{digest[:_DISPLAY_DIGEST_CHARS]}"


__all__ = [
    "ANNOTATION_ID_SCHEMA",
    "COORD_DECIMALS",
    "canonical_coord",
    "canonical_observed_value",
    "canonical_unit",
    "drawing_annotation_canonical",
    "drawing_annotation_digest",
    "drawing_annotation_id",
]
