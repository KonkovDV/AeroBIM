"""Lightweight IFC spatial index for deterministic_validation hot path.

Built once per cached ``IfcParseSession`` — guid lookup and system membership
without repeated ``model.by_type`` scans. Not a full geometry engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IfcSpatialElement:
    global_id: str
    ifc_type: str
    name: str | None
    system_ids: tuple[str, ...]


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
        except Exception:  # noqa: BLE001
            ifc_systems = []

        for system in ifc_systems:
            system_id = _system_id(system)
            member_guids: list[str] = []
            for rel in _related_objects(system):
                guid = _global_id(rel)
                if not guid:
                    continue
                member_guids.append(guid)
                ifc_type = getattr(rel, "is_a", lambda r=rel: type(r).__name__)()
                name = _optional_name(rel)
                existing = elements.get(guid)
                merged_systems: tuple[str, ...]
                if existing is None:
                    merged_systems = (system_id,)
                else:
                    merged_systems = tuple(dict.fromkeys([*existing.system_ids, system_id]))
                elements[guid] = IfcSpatialElement(
                    global_id=guid,
                    ifc_type=str(ifc_type),
                    name=name,
                    system_ids=merged_systems,
                )
            if member_guids:
                systems[system_id] = member_guids

        # Fallback: index IfcRoot entities without system assignment.
        try:
            roots = list(model.by_type("IfcRoot"))
        except Exception:  # noqa: BLE001
            roots = []
        for item in roots:
            guid = _global_id(item)
            if not guid or guid in elements:
                continue
            ifc_type = getattr(item, "is_a", lambda i=item: type(i).__name__)()
            elements[guid] = IfcSpatialElement(
                global_id=guid,
                ifc_type=str(ifc_type),
                name=_optional_name(item),
                system_ids=(),
            )

        return cls(
            elements=elements,
            systems={key: tuple(values) for key, values in systems.items()},
        )


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


__all__ = ["IfcSpatialElement", "IfcSpatialIndex"]
