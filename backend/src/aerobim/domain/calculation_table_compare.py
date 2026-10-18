"""Declared-field table compare (LIRA xlsx/docx vs RD/BIM). Not a solver.

SHA digest + per-field MATCH/MISMATCH. Native ``.lir`` is out of scope.
PDF tables stay fragile. Never flips ``calculation_correctness`` to OK.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from aerobim.domain.calculation_evidence import (
    CALCULATION_CORRECTNESS_CLAIM,
    CalculationEvidenceOutcome,
)
from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.quantity import (
    parse_localized_number,
    parse_quantity,
    si_compare,
    within_epsilon,
)

CLAIM_BOUNDARY: Final = (
    "Fixture сверка of declared fields (xlsx/docx). Not a LIRA solver. "
    "Not calculation_correctness. Native .lir not parsed. PDF remains fragile. "
    "Checkpoint GO (regulatory_measurement_mvp; customer_go false). closes_rt001/002/003=false."
)

_NUMERIC_EPS: Final = 1e-3


@dataclass(frozen=True)
class DeclaredCalcRow:
    """One declared numeric/text field from a calc sheet or a BIM/RD table.

    The observation unit is ``element_id × section_id × parameter_id``.
    A blank triple does not block a declared-field MATCH, and it is not a
    verified observation.
    """

    field_id: str
    label: str
    value: str
    unit: str
    element_id: str = ""
    section_id: str = ""
    parameter_id: str = ""


@dataclass(frozen=True)
class FieldCompare:
    field_id: str
    outcome: str
    calc_value: str | None
    bim_value: str | None
    unit: str
    observation_status: str = "NOT_VERIFIED"
    element_id: str = ""
    section_id: str = ""
    parameter_id: str = ""


@dataclass(frozen=True)
class TableCompareResult:
    calc_digest: str
    bim_digest: str
    fields: tuple[FieldCompare, ...]
    all_match: bool
    duplicate_ids: tuple[str, ...]
    solver: Literal["not_implemented"]
    claim: str
    closes_rt001: bool
    closes_rt002: bool
    closes_rt003: bool
    claim_boundary: str
    observations_complete: bool = False


def table_digest(rows: Sequence[DeclaredCalcRow]) -> str:
    """SHA-256 of the canonical row. Label is display-only; the triple is part of the identity."""

    payload = [
        {
            "element_id": row.element_id.strip(),
            "field_id": row.field_id.strip(),
            "parameter_id": row.parameter_id.strip(),
            "section_id": row.section_id.strip(),
            "unit": row.unit.strip(),
            "value": row.value.strip(),
        }
        for row in sorted(rows, key=lambda item: item.field_id)
    ]
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _index_unique(
    rows: Sequence[DeclaredCalcRow],
) -> tuple[dict[str, DeclaredCalcRow], tuple[str, ...]]:
    indexed: dict[str, DeclaredCalcRow] = {}
    duplicates: list[str] = []
    seen: set[str] = set()
    for row in rows:
        key = row.field_id.strip()
        if not key:
            continue
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
        indexed[key] = row
    return indexed, tuple(duplicates)


def _values_match(left: str, right: str, unit: str) -> bool:
    left_n = parse_localized_number(left)
    right_n = parse_localized_number(right)
    if left_n is not None and right_n is not None:
        left_q = parse_quantity(left_n, unit or "1")
        right_q = parse_quantity(right_n, unit or "1")
        if left_q.si_value is not None and right_q.si_value is not None:
            return si_compare(left_q, right_q, epsilon=_NUMERIC_EPS)
        return within_epsilon(left_n, right_n, _NUMERIC_EPS)
    return left.strip() == right.strip()


def _observation_triple(row: DeclaredCalcRow) -> tuple[str, str, str] | None:
    """Return the observation unit, or None when any coordinate is blank."""

    element = row.element_id.strip()
    section = row.section_id.strip()
    parameter = row.parameter_id.strip()
    if not element or not section or not parameter:
        return None
    return (element, section, parameter)


def _observation_status(
    calc_row: DeclaredCalcRow | None,
    bim_row: DeclaredCalcRow | None,
) -> tuple[str, str, str, str]:
    """Identify the unit. Incomplete or disagreeing triples stay NOT_VERIFIED.

    A declared-field MATCH is not promoted to a verified observation.
    """

    if calc_row is None or bim_row is None:
        return ("NOT_VERIFIED", "", "", "")
    left = _observation_triple(calc_row)
    right = _observation_triple(bim_row)
    if left is None or left != right:
        return ("NOT_VERIFIED", "", "", "")
    return ("COMPLETE", left[0], left[1], left[2])


def compare_declared_tables(
    calc_rows: Sequence[DeclaredCalcRow],
    bim_rows: Sequence[DeclaredCalcRow],
) -> TableCompareResult:
    """Compare two declared tables by field_id. MATCH is not solver correctness."""

    calc_index, calc_dupes = _index_unique(calc_rows)
    bim_index, bim_dupes = _index_unique(bim_rows)
    duplicate_ids = tuple(dict.fromkeys([*calc_dupes, *bim_dupes]))
    fields: list[FieldCompare] = []
    keys = sorted(set(calc_index) | set(bim_index))
    for key in keys:
        calc_row = calc_index.get(key)
        bim_row = bim_index.get(key)
        unit = (calc_row.unit if calc_row is not None else "") or (
            bim_row.unit if bim_row is not None else ""
        )
        if calc_row is None:
            outcome = CalculationEvidenceOutcome.SOURCE_MISSING.value
            if bim_row is not None:
                outcome = "MISSING_CALC"
        elif bim_row is None:
            outcome = "MISSING_BIM"
        elif key in duplicate_ids:
            outcome = CalculationEvidenceOutcome.MISMATCH.value
        elif _values_match(calc_row.value, bim_row.value, unit):
            outcome = CalculationEvidenceOutcome.MATCH.value
        else:
            outcome = CalculationEvidenceOutcome.MISMATCH.value
        observation_status, element_id, section_id, parameter_id = _observation_status(
            calc_row, bim_row
        )
        if key in duplicate_ids:
            observation_status = "NOT_VERIFIED"
            element_id = ""
            section_id = ""
            parameter_id = ""
        fields.append(
            FieldCompare(
                field_id=key,
                outcome=outcome,
                calc_value=None if calc_row is None else calc_row.value,
                bim_value=None if bim_row is None else bim_row.value,
                unit=unit,
                observation_status=observation_status,
                element_id=element_id,
                section_id=section_id,
                parameter_id=parameter_id,
            )
        )
    match_ok = bool(fields) and all(
        item.outcome == CalculationEvidenceOutcome.MATCH.value for item in fields
    )
    if duplicate_ids:
        match_ok = False
    return TableCompareResult(
        calc_digest=table_digest(calc_rows),
        bim_digest=table_digest(bim_rows),
        fields=tuple(fields),
        all_match=match_ok,
        duplicate_ids=duplicate_ids,
        solver="not_implemented",
        claim=CALCULATION_CORRECTNESS_CLAIM,
        closes_rt001=False,
        closes_rt002=False,
        closes_rt003=False,
        claim_boundary=CLAIM_BOUNDARY,
        observations_complete=bool(fields)
        and all(item.observation_status == "COMPLETE" for item in fields),
    )


def table_compare_honesty_snapshot() -> dict[str, object]:
    """Capabilities/honesty block: office table compare ≠ LIRA solver."""

    return {
        "artifact_type": "calculation_table_compare",
        "claim_level": "coverage_map_only",
        "checkpoint": CHECKPOINT,
        "claim": CALCULATION_CORRECTNESS_CLAIM,
        "solver": "not_implemented",
        "native_lir": "not_implemented",
        "pdf_tables": "fragile",
        "office_tables": "xlsx_docx_declared_fields",
        "observation_unit": "element_id × section_id × parameter_id",
        "incomplete_observation": "NOT_VERIFIED",
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "DeclaredCalcRow",
    "FieldCompare",
    "TableCompareResult",
    "compare_declared_tables",
    "table_compare_honesty_snapshot",
    "table_digest",
]
