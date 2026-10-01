"""Four-row calculation compare section for the export (declared values, not a solver)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from aerobim.domain.checkpoint import CHECKPOINT, CUSTOMER_GO

CLAIM_BOUNDARY: Final = (
    "Declared-value сверка between a calculation note and the model/RD. "
    "Not an independent recalculation. Not calculation_correctness. "
    "Native .lir is not parsed. Checkpoint GO; customer_go false."
)

CalcRowStatus = Literal["сверено", "нет данных в комплекте", "не поддержано"]

CALC_ROWS: Final[tuple[tuple[str, str], ...]] = (
    ("CC-1", "площадь армирования As"),
    ("CC-2", "класс бетона / стали"),
    ("CC-3", "прогибы"),
    ("CC-4", "нагрузки"),
)


def calculation_section(
    *,
    reinforcing_bar_count: int | None = None,
    compared_fields: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Always four rows. Missing rebar is an explicit no-data status, not silence.

    ``reinforcing_bar_count is None`` means this export path did not count bars.
    Do not pass ``0`` unless a count actually ran.
    """

    compared_ids = {
        str(item.get("field_id") or item.get("id") or "")
        for item in compared_fields
        if isinstance(item, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for row_id, label in CALC_ROWS:
        status: CalcRowStatus
        note: str
        if row_id == "CC-1" and (reinforcing_bar_count is None or reinforcing_bar_count <= 0):
            status = "нет данных в комплекте"
            note = (
                "IfcReinforcingBar not counted on this export path"
                if reinforcing_bar_count is None
                else "IfcReinforcingBar = 0; As from IFC is not runnable on this pack"
            )
        elif row_id in compared_ids:
            status = "сверено"
            note = "declared-field compare"
        elif row_id in {"CC-3"}:
            status = "не поддержано"
            note = "deflection vs code limit is selective; not a solver"
        else:
            status = "нет данных в комплекте"
            note = "no declared calc table on this run"
        rows.append({"id": row_id, "label": label, "status": status, "note": note})
    return {
        "artifact_type": "calculation_section",
        "schema_version": "1.0.0",
        "claim_boundary": CLAIM_BOUNDARY,
        "independent_recalculation": False,
        "checkpoint": CHECKPOINT,
        "customer_go": CUSTOMER_GO,
        "rows": rows,
    }
