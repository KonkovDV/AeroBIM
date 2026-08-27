"""Lightweight IFC spatial index for deterministic_validation hot path.

Built once per cached ``IfcParseSession`` — guid lookup, system membership,
and containment storey / referenced grid axis without repeated ``model.by_type``
scans. Not a full geometry engine. Axis is **not** inferred from drawing OCR.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from aerobim.domain.models import ValidationIssue


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
    "stamp_issues_with_spatial_location",
]
