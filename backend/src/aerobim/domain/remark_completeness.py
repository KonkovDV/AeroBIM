"""Remark completeness against customer answer 2.1.5 (essence + clause + location).

Counts are coverage of the remark *shape*, not product accuracy.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from aerobim.domain.finding_layer import classify_finding_layer, issue_as_mapping
from aerobim.domain.remark_shape import UNBOUND_MARKERS

CLAIM_LEVEL: Final = "coverage_map_only"
CLAIM_BOUNDARY: Final = (
    "Share of pack_finding rows that carry essence + bound clause + location. "
    "Not product accuracy. Not TZ >90%. Checkpoint GO; customer_go false."
)

UNBOUND_LOCATION_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "без точной привязки",
        "no precise location",
    }
)


def _text(value: object) -> str:
    return str(value).strip() if value not in (None, "") else ""


def _is_unbound_clause(cite: str, *, bound: object) -> bool:
    if not cite:
        return True
    if cite.casefold() in {marker.casefold() for marker in UNBOUND_MARKERS}:
        return True
    return bound is False


def _is_unbound_location(line: str) -> bool:
    if not line:
        return True
    return line.casefold() in {marker.casefold() for marker in UNBOUND_LOCATION_MARKERS}


def remark_completeness(item: Any) -> dict[str, bool]:
    mapping = issue_as_mapping(item)
    remark = mapping.get("remark") if isinstance(mapping.get("remark"), Mapping) else {}
    essence = _text(remark.get("essence") if isinstance(remark, Mapping) else "")
    if not essence:
        title = _text(remark.get("title") if isinstance(remark, Mapping) else "")
        essence = title
    has_essence = bool(essence) or bool(_text(mapping.get("message")))
    cite = _text(remark.get("clause_cite") if isinstance(remark, Mapping) else "")
    if not cite:
        cite = _text(mapping.get("norm_clause"))
    bound = remark.get("clause_bound") if isinstance(remark, Mapping) else None
    has_clause = not _is_unbound_clause(cite, bound=bound)
    location_line = _text(remark.get("location_line") if isinstance(remark, Mapping) else "")
    if not location_line:
        location_line = _text(mapping.get("storey_name") or mapping.get("grid_axis"))
    zone = mapping.get("problem_zone")
    sheet = _text(zone.get("sheet_id") if isinstance(zone, Mapping) else "")
    has_location = (bool(location_line) and not _is_unbound_location(location_line)) or bool(
        _text(mapping.get("storey_name")) or _text(mapping.get("grid_axis")) or sheet
    )
    has_object = bool(
        _text(mapping.get("element_guid")) or _text(mapping.get("target_ref")) or sheet
    )
    return {
        "has_essence": has_essence,
        "has_clause": has_clause,
        "has_location": has_location,
        "has_object": has_object,
        "full_triad": has_essence and has_clause and has_location,
    }


def incomplete_marker(item: Any, *, locale: str = "ru") -> str:
    flags = remark_completeness(item)
    if flags["full_triad"]:
        return ""
    missing: list[str] = []
    if locale == "en":
        if not flags["has_clause"]:
            missing.append("no clause")
        if not flags["has_location"]:
            missing.append("no location")
        if not flags["has_essence"]:
            missing.append("no essence")
        return "incomplete remark: " + " / ".join(missing)
    if not flags["has_clause"]:
        missing.append("нет пункта")
    if not flags["has_location"]:
        missing.append("нет локации")
    if not flags["has_essence"]:
        missing.append("нет сути")
    return "неполное замечание: " + " / ".join(missing)


def completeness_table(issues: Sequence[Any]) -> dict[str, Any]:
    pack = [item for item in issues if classify_finding_layer(item) == "pack_finding"]
    total = len(pack)
    flags = [remark_completeness(item) for item in pack]

    def _share(key: str) -> float:
        if total == 0:
            return 0.0
        return round(sum(1 for row in flags if row[key]) / total, 4)

    return {
        "artifact_type": "remark_completeness",
        "claim_level": CLAIM_LEVEL,
        "is_accuracy": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "pack_finding_count": total,
        "full_triad_count": sum(1 for row in flags if row["full_triad"]),
        "share_full_triad": _share("full_triad"),
        "share_has_clause": _share("has_clause"),
        "share_has_location": _share("has_location"),
        "share_has_essence": _share("has_essence"),
    }


__all__ = [
    "CLAIM_BOUNDARY",
    "CLAIM_LEVEL",
    "UNBOUND_LOCATION_MARKERS",
    "completeness_table",
    "incomplete_marker",
    "remark_completeness",
]
