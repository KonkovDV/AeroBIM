"""Customer remark shape (answers п. 2.1.5) as a checkable payload, not a prose agreement.

Essence (one sentence) + bound norm/STO clause or an explicit unbound marker +
location (storey / axis / sheet / GUID). Unbound is honesty, not an invented cite.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from aerobim.domain.models import GeneratedRemark, ValidationIssue

UNBOUND_CLAUSE_RU = "пункт нормы не привязан"
UNBOUND_CLAUSE_EN = "no bound clause (not invented)"
UNBOUND_MARKERS = frozenset({UNBOUND_CLAUSE_RU, UNBOUND_CLAUSE_EN})

GATE_CLASSES = frozenset({"schema", "quality", "regulatory"})
ANSWER_NATURES = frozenset({"deterministic", "probabilistic"})


@dataclass(frozen=True)
class RemarkLocation:
    line: str
    storey_name: str | None = None
    grid_axis: str | None = None
    sheet_id: str | None = None
    element_guid: str | None = None


@dataclass(frozen=True)
class RemarkShape:
    essence: str
    clause_cite: str
    clause_bound: bool
    location: RemarkLocation
    detail: str
    gate_class: str | None = None
    answer_nature: str | None = None

    def as_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def validate_remark_shape(payload: dict[str, Any]) -> list[str]:
    """Return human-readable violations. Empty list means the payload is shaped."""

    errors: list[str] = []
    essence = str(payload.get("essence") or "").strip()
    if not essence:
        errors.append("essence missing")
    clause = str(payload.get("clause_cite") or "").strip()
    if not clause:
        errors.append("clause_cite missing")
    bound = payload.get("clause_bound")
    if not isinstance(bound, bool):
        errors.append("clause_bound must be bool")
    elif bound and clause.casefold() in {marker.casefold() for marker in UNBOUND_MARKERS}:
        errors.append("clause_bound true but cite is the unbound marker")
    elif (
        not bound
        and clause
        and clause.casefold() not in {marker.casefold() for marker in UNBOUND_MARKERS}
    ):
        errors.append("clause_bound false but cite is not the unbound marker")
    location = payload.get("location")
    if not isinstance(location, dict):
        errors.append("location missing")
    else:
        line = str(location.get("line") or "").strip()
        if not line:
            errors.append("location.line missing")
    detail = str(payload.get("detail") or "").strip()
    if not detail:
        errors.append("detail missing")
    gate = payload.get("gate_class")
    if gate is not None and gate not in GATE_CLASSES:
        errors.append("gate_class invalid")
    nature = payload.get("answer_nature")
    if nature is not None and nature not in ANSWER_NATURES:
        errors.append("answer_nature invalid")
    return errors


def shape_from_remark(
    remark: GeneratedRemark,
    *,
    gate_class: str | None = None,
    answer_nature: str | None = None,
) -> RemarkShape:
    location = RemarkLocation(
        line=str(getattr(remark, "location_line", "") or ""),
        storey_name=getattr(remark, "storey_name", None),
        grid_axis=getattr(remark, "grid_axis", None),
        sheet_id=getattr(remark, "sheet_id", None),
        element_guid=getattr(remark, "element_guid", None),
    )
    return RemarkShape(
        essence=str(getattr(remark, "essence", "") or ""),
        clause_cite=str(getattr(remark, "clause_cite", "") or ""),
        clause_bound=bool(getattr(remark, "clause_bound", False)),
        location=location,
        detail=str(getattr(remark, "detail", "") or ""),
        gate_class=gate_class,
        answer_nature=answer_nature,
    )


def merge_advisory_onto_template(
    template: GeneratedRemark | None, draft: GeneratedRemark
) -> GeneratedRemark:
    """Keep bound clause/location from the engine; LLM text stays in body/detail."""

    from dataclasses import replace

    if template is None:
        return draft
    return replace(
        draft,
        essence=template.essence or draft.essence,
        clause_cite=template.clause_cite or draft.clause_cite,
        clause_bound=template.clause_bound,
        location_line=template.location_line or draft.location_line,
        detail=draft.body or template.detail,
        storey_name=template.storey_name,
        grid_axis=template.grid_axis,
        sheet_id=template.sheet_id,
        element_guid=template.element_guid,
    )


def shape_from_issue(issue: ValidationIssue) -> RemarkShape | None:
    remark = issue.remark
    if remark is None:
        return None
    return shape_from_remark(
        remark,
        gate_class=getattr(issue, "gate_class", None),
        answer_nature=getattr(issue, "answer_nature", None),
    )


__all__ = [
    "ANSWER_NATURES",
    "GATE_CLASSES",
    "RemarkLocation",
    "RemarkShape",
    "UNBOUND_CLAUSE_EN",
    "UNBOUND_CLAUSE_RU",
    "UNBOUND_MARKERS",
    "merge_advisory_onto_template",
    "shape_from_issue",
    "shape_from_remark",
    "validate_remark_shape",
]
