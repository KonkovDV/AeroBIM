"""Finding volume table — tracker SIG-01 metric shape.

A raw machine-record count is not product accuracy, not TZ >90%, not
«пакет обработан», and not a customer defect list. Checkpoint NO_GO.

Mandated report phrase: «объём находок на канале получен».
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final

from aerobim.domain.target_ref import UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER

CLAIM_LEVEL: Final = "pack_volume_not_accuracy"
CHECKPOINT: Final = "NO_GO"
REPORT_PHRASE: Final = "объём находок на канале получен"
CLAIM_BOUNDARY: Final = (
    "Finding volume and type breakdown on this pack. "
    "Report phrase: объём находок на канале получен. "
    "Not product accuracy. Not pack processed. Not a customer defect list. "
    "Not TZ >90%. Not dual-rater precision. Checkpoint NO_GO."
)

# Rule ids that are not element defects: HITL queue, capability flags, unsigned
# advisory inventory, and (when the GUID is a real IfcRoot GlobalId) integrity.
_RULE_VOLUME_CLASS: Final[dict[str, str]] = {
    "AEROBIM-DRAWING-REGION-HITL": "service_hitl",
    "AEROBIM-CLASH-CAPABILITY": "service_capability",
    "AEROBIM-IDS-CAPABILITY": "service_capability",
    "AEROBIM-SPACE-EFFICIENCY-CANDIDATE": "advisory_unsigned",
    "AEROBIM-GUID-DUPLICATE": "data_integrity",
    "AEROBIM-IFC-GUID-DUPLICATE": "data_integrity",
    "AEROBIM-IFC-GUID-INVALID": "data_integrity",
    "AEROBIM-IFC-SCHEMA": "data_integrity",
    "AEROBIM-IFC-SCHEMA-UNSUPPORTED": "data_integrity",
    "AEROBIM-UNIT-SCALE": "service_capability",
    "AEROBIM-QTY-MISSING": "coverage_unsigned",
    "AEROBIM-QTY-MISMATCH": "coverage_unsigned",
}

# HITL + capability flags are machine records, not findings.
_NON_FINDING_CLASSES: Final[frozenset[str]] = frozenset({"service_hitl", "service_capability"})


def classify_volume_record(item: Mapping[str, Any]) -> str:
    """Classify one machine record for SIG-01 honesty (not accuracy)."""

    rule_id = str(item.get("rule_id") or "")
    mapped = _RULE_VOLUME_CLASS.get(rule_id)
    if mapped is not None:
        return mapped
    origin = str(item.get("origin") or "").strip().lower()
    if origin == "advisory":
        return "advisory_unsigned"
    message = str(item.get("message") or "")
    if "No elements found for entity" in message:
        return "entity_presence"
    if UNRESTRICTED_MISMATCH_SUPPRESSOR_MARKER in message:
        return "coverage_unsigned"
    if "was not found on any" in message or "is missing on" in message:
        return "coverage_unsigned"
    if "Quantity mismatch" in message and " of " in message:
        return "coverage_unsigned"
    if item.get("element_guid"):
        return "element_detection_unsigned"
    if rule_id == "SAM-AR-020":
        return "element_detection_unsigned"
    if rule_id.startswith("SAM-AR-"):
        return "coverage_unsigned"
    if rule_id.startswith(("REQ-FIRE-", "REQ-STR-", "REQ-MEP-", "REQ-HEIGHT-")):
        return "unsigned_universal_rule"
    return "engine_record"


def volume_from_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build the tracker table from finding dicts (gate JSON or HTTP report)."""

    by_type: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    by_volume_class: Counter[str] = Counter()
    for item in findings:
        if not isinstance(item, Mapping):
            continue
        kind = str(
            item.get("category") or item.get("maps_to_category") or item.get("rule_id") or "untyped"
        )
        by_type[kind] += 1
        by_severity[str(item.get("severity") or "unspecified")] += 1
        by_volume_class[classify_volume_record(item)] += 1
    total = sum(by_type.values())
    non_finding = sum(by_volume_class[cls] for cls in _NON_FINDING_CLASSES)
    return {
        "artifact_type": "finding_volume",
        "claim_level": CLAIM_LEVEL,
        "checkpoint": CHECKPOINT,
        "closes_rt001": False,
        "closes_rt002": False,
        "closes_rt003": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "report_phrase": REPORT_PHRASE,
        "is_accuracy": False,
        "is_pack_processed": False,
        "is_customer_defect_list": False,
        "total": total,
        "machine_record_count": total,
        "service_record_count": non_finding,
        "by_type": dict(by_type),
        "by_severity": dict(by_severity),
        "by_volume_class": dict(by_volume_class),
    }


def volume_from_issues(issues: Sequence[Any]) -> dict[str, Any]:
    """Same table as ``volume_from_findings``, from ``ValidationIssue`` or dicts."""

    rows: list[Mapping[str, Any]] = []
    for item in issues:
        if isinstance(item, Mapping):
            rows.append(item)
            continue
        rows.append(
            {
                "rule_id": getattr(item, "rule_id", None),
                "severity": getattr(getattr(item, "severity", None), "value", None)
                or getattr(item, "severity", None),
                "message": getattr(item, "message", None),
                "category": getattr(getattr(item, "category", None), "value", None)
                or getattr(item, "category", None),
                "element_guid": getattr(item, "element_guid", None),
                "origin": getattr(item, "origin", None),
            }
        )
    return volume_from_findings(rows)


__all__ = [
    "CLAIM_BOUNDARY",
    "CHECKPOINT",
    "REPORT_PHRASE",
    "classify_volume_record",
    "volume_from_findings",
    "volume_from_issues",
]
