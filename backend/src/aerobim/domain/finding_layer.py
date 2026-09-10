"""Presentation layer of a machine record — grouping, not a verdict.

Layers never change ``severity``, ``priority``, ``summary.passed`` or the
stored ``issues`` list. Checkpoint GO; ``customer_go`` false.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final, Literal

from aerobim.domain.finding_volume import classify_volume_record
from aerobim.domain.remark_shape import UNBOUND_MARKERS

FindingLayer = Literal[
    "pack_finding",
    "coverage_note",
    "service_record",
    "advisory_candidate",
]

FINDING_LAYER_ORDER: Final[tuple[FindingLayer, ...]] = (
    "pack_finding",
    "coverage_note",
    "service_record",
    "advisory_candidate",
)

CLAIM_BOUNDARY: Final = (
    "Presentation grouping of machine records into layers. "
    "Not product accuracy. Not a customer defect list. Not TZ >90%. "
    "Does not change summary.passed. Checkpoint GO; customer_go false."
)

LAYER_LABELS_RU: Final[dict[FindingLayer, str]] = {
    "pack_finding": "Замечания к комплекту",
    "coverage_note": "Проверки без объектов проверки",
    "service_record": "Служебные записи",
    "advisory_candidate": "Кандидаты, требующие согласования критерия",
}

LAYER_LABELS_EN: Final[dict[FindingLayer, str]] = {
    "pack_finding": "Pack findings",
    "coverage_note": "Checks without checkable objects",
    "service_record": "Service records",
    "advisory_candidate": "Candidates awaiting a criterion",
}

LAYER_NOTES_RU: Final[dict[FindingLayer, str]] = {
    "pack_finding": (
        "Запись адресует объект комплекта и имеет основание "
        "(норма, IDS или правило). Не точность продукта."
    ),
    "coverage_note": (
        "Проверка не состоялась или нет объектов проверки. Это не «нарушений не найдено»."
    ),
    "service_record": "Очередь HITL и отказы движка. Не замечания к комплекту.",
    "advisory_candidate": ("Недетерминированный кандидат. Не пишет summary.passed (ADR-001)."),
}

LAYER_NOTES_EN: Final[dict[FindingLayer, str]] = {
    "pack_finding": (
        "The row addresses a pack object and has a basis "
        "(clause, IDS, or requirement rule). Not product accuracy."
    ),
    "coverage_note": ("The check did not run or had no objects. Not the same as 'no defects'."),
    "service_record": "HITL queue and engine refusals. Not pack findings.",
    "advisory_candidate": ("Advisory candidate. Never writes summary.passed (ADR-001)."),
}

TzSection = Literal[
    "norms_and_tz",
    "geometric_clash",
    "logical_clash",
    "calculation",
    "area",
    "space_efficiency",
]

TZ_SECTION_ORDER: Final[tuple[TzSection, ...]] = (
    "norms_and_tz",
    "geometric_clash",
    "logical_clash",
    "calculation",
    "area",
    "space_efficiency",
)

TZ_SECTION_LABELS_RU: Final[dict[TzSection, str]] = {
    "norms_and_tz": "Несоответствия нормам и ТЗ",
    "geometric_clash": "Коллизии геометрические",
    "logical_clash": "Коллизии логические (объёмы: спецификация ↔ график ↔ BIM)",
    "calculation": "Сверка с расчётом",
    "area": "Площади",
    "space_efficiency": "Неэффективное использование пространства",
}

TZ_SECTION_LABELS_EN: Final[dict[TzSection, str]] = {
    "norms_and_tz": "Norm and brief mismatches",
    "geometric_clash": "Geometric clashes",
    "logical_clash": "Logical clashes (quantities: spec ↔ schedule ↔ BIM)",
    "calculation": "Calculation comparison",
    "area": "Areas",
    "space_efficiency": "Inefficient use of space",
}

_VOLUME_TO_LAYER: Final[dict[str, FindingLayer]] = {
    "advisory_unsigned": "advisory_candidate",
    "service_hitl": "service_record",
    "service_capability": "service_record",
    "entity_presence": "coverage_note",
    "coverage_unsigned": "coverage_note",
    "unrestricted_eq_sample": "coverage_note",
    "element_detection_unsigned": "pack_finding",
    "unsigned_universal_rule": "pack_finding",
    "data_integrity": "pack_finding",
}

_ENGINE_NON_REQUIREMENT_PREFIXES: Final[tuple[str, ...]] = (
    "AEROBIM-LOAD-",
    "AEROBIM-DRAWING-REGION-HITL",
    "AEROBIM-CLASH-CAPABILITY",
    "AEROBIM-IDS-CAPABILITY",
    "AEROBIM-UNIT-SCALE",
    "AEROBIM-SPACE-EFFICIENCY-",
    "AEROBIM-QTY-",
)

HITL_RULE_ID: Final = "AEROBIM-DRAWING-REGION-HITL"


def issue_as_mapping(item: Any) -> dict[str, Any]:
    """Dict view of a serialized issue or ``ValidationIssue`` for classifiers."""

    if isinstance(item, Mapping):
        return dict(item)
    remark = getattr(item, "remark", None)
    remark_map: dict[str, Any] | None = None
    if remark is not None:
        remark_map = {
            "clause_cite": getattr(remark, "clause_cite", None),
            "clause_bound": getattr(remark, "clause_bound", None),
            "essence": getattr(remark, "essence", None),
            "title": getattr(remark, "title", None),
            "location_line": getattr(remark, "location_line", None),
            "body": getattr(remark, "body", None),
        }
    zone = getattr(item, "problem_zone", None)
    zone_map: dict[str, Any] | None = None
    if zone is not None:
        zone_map = {"sheet_id": getattr(zone, "sheet_id", None)}
    review = getattr(item, "review", None)
    return {
        "rule_id": getattr(item, "rule_id", None),
        "severity": getattr(getattr(item, "severity", None), "value", None)
        or getattr(item, "severity", None),
        "priority": getattr(item, "priority", None),
        "message": getattr(item, "message", None),
        "category": getattr(getattr(item, "category", None), "value", None)
        or getattr(item, "category", None),
        "element_guid": getattr(item, "element_guid", None),
        "origin": getattr(item, "origin", None),
        "target_ref": getattr(item, "target_ref", None),
        "norm_clause": getattr(item, "norm_clause", None),
        "norm_source": getattr(item, "norm_source", None),
        "finding_id": getattr(item, "finding_id", None),
        "source_id": getattr(item, "source_id", None),
        "problem_zone": zone_map,
        "remark": remark_map,
        "review": review if isinstance(review, Mapping) else None,
        "storey_name": getattr(item, "storey_name", None),
        "grid_axis": getattr(item, "grid_axis", None),
    }


def _text(value: object) -> str:
    return str(value).strip() if value not in (None, "") else ""


def has_addressable_object(item: Mapping[str, Any]) -> bool:
    if _text(item.get("element_guid")):
        return True
    if _text(item.get("target_ref")):
        return True
    zone = item.get("problem_zone")
    if isinstance(zone, Mapping) and _text(zone.get("sheet_id")):
        return True
    refs = item.get("evidence_refs") or ()
    if isinstance(refs, (list, tuple)):
        for ref in refs:
            text = _text(ref)
            if text and not text.startswith("triage:"):
                return True
    return False


def _cite_is_bound(item: Mapping[str, Any]) -> bool:
    if _text(item.get("norm_clause")):
        return True
    remark = item.get("remark")
    if not isinstance(remark, Mapping):
        return False
    cite = _text(remark.get("clause_cite"))
    if not cite:
        return False
    if cite.casefold() in {marker.casefold() for marker in UNBOUND_MARKERS}:
        return False
    bound = remark.get("clause_bound")
    if bound is False:
        return False
    return True


def _is_requirement_rule(rule_id: str) -> bool:
    if not rule_id:
        return False
    upper = rule_id.upper()
    for prefix in _ENGINE_NON_REQUIREMENT_PREFIXES:
        if upper.startswith(prefix) or rule_id.startswith(prefix):
            return False
    if rule_id.startswith(("REQ-", "SAM-", "IDS-", "SPATIAL-", "SP-", "FIRE-")):
        return True
    if rule_id.startswith("AEROBIM-"):
        return False
    return True


def has_requirement_basis(item: Mapping[str, Any]) -> bool:
    if _cite_is_bound(item):
        return True
    return _is_requirement_rule(_text(item.get("rule_id")))


def _positive_pack_finding(item: Mapping[str, Any]) -> bool:
    return has_addressable_object(item) and has_requirement_basis(item)


def classify_finding_layer(item: Any) -> FindingLayer:
    """Map a volume class to a presentation layer (RT-PLAN-17)."""

    mapping = issue_as_mapping(item)
    volume = classify_volume_record(mapping)
    mapped = _VOLUME_TO_LAYER.get(volume)
    if mapped is not None:
        return mapped
    if _positive_pack_finding(mapping):
        return "pack_finding"
    return "coverage_note"


def classify_tz_section(item: Any) -> TzSection:
    mapping = issue_as_mapping(item)
    rule_id = _text(mapping.get("rule_id")).upper()
    category = _text(mapping.get("category")).lower()
    message = _text(mapping.get("message")).lower()
    if "SPACE-EFFICIENCY" in rule_id:
        return "space_efficiency"
    if category == "spatial" or rule_id.startswith("SPATIAL-") or "CLASH" in rule_id:
        return "geometric_clash"
    if rule_id.startswith("AEROBIM-LOAD-") or rule_id.startswith("OPENREBAR-"):
        return "calculation"
    if "QTY" in rule_id or "quantity mismatch" in message:
        return "logical_clash"
    if "AREA" in rule_id or "netfloorarea" in message or "netfloorarea" in rule_id.lower():
        return "area"
    return "norms_and_tz"


def layer_counts(issues: Sequence[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in issues:
        counts[classify_finding_layer(item)] += 1
    return {layer: int(counts.get(layer, 0)) for layer in FINDING_LAYER_ORDER}


def layer_labels(locale: str) -> dict[FindingLayer, str]:
    return LAYER_LABELS_EN if locale == "en" else LAYER_LABELS_RU


def layer_notes(locale: str) -> dict[FindingLayer, str]:
    return LAYER_NOTES_EN if locale == "en" else LAYER_NOTES_RU


def tz_section_labels(locale: str) -> dict[TzSection, str]:
    return TZ_SECTION_LABELS_EN if locale == "en" else TZ_SECTION_LABELS_RU


__all__ = [
    "CLAIM_BOUNDARY",
    "FINDING_LAYER_ORDER",
    "HITL_RULE_ID",
    "FindingLayer",
    "LAYER_LABELS_EN",
    "LAYER_LABELS_RU",
    "LAYER_NOTES_EN",
    "LAYER_NOTES_RU",
    "TZ_SECTION_LABELS_EN",
    "TZ_SECTION_LABELS_RU",
    "TZ_SECTION_ORDER",
    "TzSection",
    "classify_finding_layer",
    "classify_tz_section",
    "has_addressable_object",
    "has_requirement_basis",
    "issue_as_mapping",
    "layer_counts",
    "layer_labels",
    "layer_notes",
    "tz_section_labels",
]
