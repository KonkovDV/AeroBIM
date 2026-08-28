"""Lightweight IFC spatial index for deterministic_validation hot path.

Built once per cached ``IfcParseSession`` — guid lookup, system membership,
and containment storey / referenced grid axis without repeated ``model.by_type``
scans. Not a full geometry engine. Axis is **not** inferred from drawing OCR.
JSON sidecar dump is optional and is **not** a disk R-tree or analyze input.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final

from aerobim.domain.models import ValidationIssue

SIDECAR_CLAIM: Final = (
    "JSON dump of in-memory IfcSpatialIndex. Not a disk R-tree. "
    "Not a streaming parser. Not wired into analyze. Does not raise the IFC cap."
)
SIDECAR_ARTIFACT_TYPE: Final = "ifc_spatial_index_sidecar"


@dataclass(frozen=True)
class IfcSpatialElement:
    global_id: str
    ifc_type: str
    name: str | None
    system_ids: tuple[str, ...]
    storey_name: str | None = None
    grid_axis: str | None = None


@dataclass(frozen=True)
class IfcSpatialIndex:
    elements: dict[str, IfcSpatialElement]
    systems: dict[str, tuple[str, ...]]

    def lookup(self, global_id: str) -> IfcSpatialElement | None:
        return self.elements.get(global_id)

    def system_members(self, system_id: str) -> tuple[str, ...]:
        return self.systems.get(system_id, ())

    @classmethod
    def from_model(cls, model: Any) -> IfcSpatialIndex:
        elements: dict[str, IfcSpatialElement] = {}
        systems: dict[str, list[str]] = {}

        try:
            ifc_systems = list(model.by_type("IfcSystem"))
        except Exception:
            ifc_systems = []

        for system in ifc_systems:
            system_id = _system_id(system)
            member_guids: list[str] = []
            for rel in _related_objects(system):
                guid = _global_id(rel)
                if not guid:
                    continue
                member_guids.append(guid)
                elements[guid] = _merge_element(elements.get(guid), rel, extra_system=system_id)
            if member_guids:
                systems[system_id] = member_guids

        # Fallback: index IfcRoot entities without system assignment; also fill
        # storey/axis on system members that were seen before containment walk.
        try:
            roots = list(model.by_type("IfcRoot"))
        except Exception:
            roots = []
        for item in roots:
            guid = _global_id(item)
            if not guid:
                continue
            elements[guid] = _merge_element(elements.get(guid), item, extra_system=None)

        return cls(
            elements=elements,
            systems={key: tuple(values) for key, values in systems.items()},
        )


def write_spatial_index_json(index: IfcSpatialIndex, path: Path) -> None:
    """Write a JSON dump of the in-memory index. Not a disk R-tree."""

    payload = {
        "artifact_type": SIDECAR_ARTIFACT_TYPE,
        "claim_boundary": SIDECAR_CLAIM,
        "disk_r_tree": False,
        "streaming_parser": False,
        "wired_into_analyze": False,
        "raises_default_cap": False,
        "closes_rt001": False,
        "elements": [
            {
                "global_id": element.global_id,
                "ifc_type": element.ifc_type,
                "name": element.name,
                "system_ids": list(element.system_ids),
                "storey_name": element.storey_name,
                "grid_axis": element.grid_axis,
            }
            for element in index.elements.values()
        ],
        "systems": {key: list(values) for key, values in index.systems.items()},
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_spatial_index_json(path: Path) -> IfcSpatialIndex:
    """Load a sidecar written by ``write_spatial_index_json``.

    Rejects payloads that claim a disk R-tree or streaming parser.
    """

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("spatial index sidecar must be a JSON object")
    if raw.get("artifact_type") != SIDECAR_ARTIFACT_TYPE:
        raise ValueError("not an IfcSpatialIndex sidecar")
    if raw.get("disk_r_tree") is True:
        raise ValueError("sidecar must not claim disk_r_tree")
    if raw.get("streaming_parser") is True:
        raise ValueError("sidecar must not claim streaming_parser")
    elements: dict[str, IfcSpatialElement] = {}
    for item in raw.get("elements") or []:
        if not isinstance(item, dict):
            continue
        guid = str(item.get("global_id") or "").strip()
        if not guid:
            continue
        name_raw = item.get("name")
        storey_raw = item.get("storey_name")
        axis_raw = item.get("grid_axis")
        systems = item.get("system_ids") or ()
        elements[guid] = IfcSpatialElement(
            global_id=guid,
            ifc_type=str(item.get("ifc_type") or ""),
            name=None if name_raw is None else str(name_raw),
            system_ids=tuple(str(value) for value in systems),
            storey_name=None if storey_raw is None else str(storey_raw),
            grid_axis=None if axis_raw is None else str(axis_raw),
        )
    systems: dict[str, tuple[str, ...]] = {}
    for key, values in (raw.get("systems") or {}).items():
        systems[str(key)] = tuple(str(value) for value in values)
    return IfcSpatialIndex(elements=elements, systems=systems)


def stamp_issues_with_spatial_location(
    issues: Sequence[ValidationIssue],
    index: Any | None,
) -> tuple[ValidationIssue, ...]:
    """Copy storey/axis from the spatial index when a GUID hits.

    Misses stay ``None``. Template remarks then say the index has no storey/axis
    rather than inventing text from OCR or the LLM. Does not change
    ``finding_id`` (provenance hash ignores these fields).
    """

    if index is None or not hasattr(index, "lookup"):
        return tuple(issues)
    stamped: list[ValidationIssue] = []
    for issue in issues:
        guid = issue.element_guid
        if not guid and issue.problem_zone is not None:
            guid = issue.problem_zone.element_guid
        if not guid:
            stamped.append(issue)
            continue
        hit = index.lookup(guid)
        if hit is None:
            stamped.append(issue)
            continue
        storey = getattr(hit, "storey_name", None)
        axis = getattr(hit, "grid_axis", None)
        if not storey and not axis:
            stamped.append(issue)
            continue
        stamped.append(
            replace(
                issue,
                storey_name=storey or issue.storey_name,
                grid_axis=axis or issue.grid_axis,
            )
        )
    return tuple(stamped)


def _merge_element(
    existing: IfcSpatialElement | None,
    entity: Any,
    *,
    extra_system: str | None,
) -> IfcSpatialElement:
    guid = _global_id(entity) or (existing.global_id if existing else "")
    ifc_type = _ifc_type(entity)
    name = _optional_name(entity)
    storey, axis = _spatial_location(entity)
    systems: tuple[str, ...]
    if existing is None:
        systems = (extra_system,) if extra_system else ()
    else:
        merged = list(existing.system_ids)
        if extra_system:
            merged.append(extra_system)
        systems = tuple(dict.fromkeys(merged))
        ifc_type = existing.ifc_type or ifc_type
        name = existing.name or name
        storey = existing.storey_name or storey
        axis = existing.grid_axis or axis
    return IfcSpatialElement(
        global_id=guid,
        ifc_type=str(ifc_type),
        name=name,
        system_ids=systems,
        storey_name=storey,
        grid_axis=axis,
    )


def _spatial_location(entity: Any) -> tuple[str | None, str | None]:
    return _containing_storey_name(entity), _referenced_grid_axis(entity)


def _containing_storey_name(entity: Any, *, _seen: set[int] | None = None) -> str | None:
    if entity is None:
        return None
    marker = id(entity)
    seen = _seen if _seen is not None else set()
    if marker in seen:
        return None
    seen.add(marker)
    if _ifc_type(entity) == "IfcBuildingStorey":
        return _optional_name(entity)
    for rel in getattr(entity, "ContainedInStructure", None) or []:
        found = _containing_storey_name(
            getattr(rel, "RelatingStructure", None),
            _seen=seen,
        )
        if found:
            return found
    for rel in getattr(entity, "Decomposes", None) or []:
        found = _containing_storey_name(
            getattr(rel, "RelatingObject", None),
            _seen=seen,
        )
        if found:
            return found
    return None


def _referenced_grid_axis(entity: Any) -> str | None:
    """IfcGridAxis.AxisTag only. IfcGrid.Name is not an axis tag — leave empty."""

    for rel in getattr(entity, "ReferencedInStructures", None) or []:
        relating = getattr(rel, "RelatingStructure", None)
        if relating is None:
            continue
        if _ifc_type(relating) != "IfcGridAxis":
            continue
        tag = getattr(relating, "AxisTag", None)
        if tag is not None and str(tag).strip():
            return str(tag).strip()
        named = _optional_name(relating)
        if named:
            return named
    return None


def _ifc_type(entity: Any) -> str:
    is_a = getattr(entity, "is_a", None)
    if callable(is_a):
        try:
            return str(is_a())
        except Exception:
            return type(entity).__name__
    return type(entity).__name__


def _global_id(entity: Any) -> str | None:
    raw = getattr(entity, "GlobalId", None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _optional_name(entity: Any) -> str | None:
    raw = getattr(entity, "Name", None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _system_id(system: Any) -> str:
    name = _optional_name(system)
    if name:
        return name
    guid = _global_id(system)
    if guid:
        return guid
    return "IfcSystem"


def _related_objects(system: Any) -> list[Any]:
    objects: list[Any] = []
    for rel in getattr(system, "IsGroupedBy", None) or []:
        related = getattr(rel, "RelatedObjects", None) or []
        objects.extend(related)
    return objects


__all__ = [
    "IfcSpatialElement",
    "IfcSpatialIndex",
    "SIDECAR_CLAIM",
    "read_spatial_index_json",
    "stamp_issues_with_spatial_location",
    "write_spatial_index_json",
]
