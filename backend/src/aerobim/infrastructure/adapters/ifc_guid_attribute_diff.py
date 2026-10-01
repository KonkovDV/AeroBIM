"""GUID / simple-attribute IFC model diff without deepdiff.

Uses IfcOpenShell already declared in the stack. Covers add/remove by GlobalId
and a small attribute set (Name, ObjectType, Tag, Description).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aerobim.domain.ifc_model_diff import (
    IfcModelDiffEntry,
    IfcModelDiffResult,
)
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_model

_COMPARE_ATTRS = ("Name", "ObjectType", "Tag", "Description")
_SKIP_TYPES = frozenset(
    {
        "IfcOwnerHistory",
        "IfcApplication",
        "IfcPerson",
        "IfcOrganization",
        "IfcPersonAndOrganization",
        "IfcCartesianPoint",
        "IfcDirection",
        "IfcAxis2Placement2D",
        "IfcAxis2Placement3D",
        "IfcLocalPlacement",
        "IfcGeometricRepresentationContext",
        "IfcGeometricRepresentationSubContext",
        "IfcShapeRepresentation",
        "IfcProductDefinitionShape",
        "IfcUnitAssignment",
        "IfcSIUnit",
        "IfcConversionBasedUnit",
        "IfcMeasureWithUnit",
        "IfcDimensionalExponents",
        "IfcPropertySingleValue",
        "IfcPropertySet",
        "IfcRelDefinesByProperties",
        "IfcRelAggregates",
        "IfcRelContainedInSpatialStructure",
        "IfcRelDefinesByType",
    }
)


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _inventory(model: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for el in model:
        guid = getattr(el, "GlobalId", None)
        if not guid or not isinstance(guid, str):
            continue
        ifc_type = el.is_a()
        if ifc_type in _SKIP_TYPES:
            continue
        out[guid] = el
    return out


class IfcGuidAttributeDiffAdapter:
    """Thin ``IfcModelDiff`` adapter — no deepdiff / ifcdiff CLI required."""

    def compare(self, old_ifc: Path, new_ifc: Path) -> IfcModelDiffResult:
        old_model = open_ifc_model(Path(old_ifc))
        new_model = open_ifc_model(Path(new_ifc))
        old_inv = _inventory(old_model)
        new_inv = _inventory(new_model)

        entries: list[IfcModelDiffEntry] = []
        for guid in sorted(set(old_inv) - set(new_inv)):
            el = old_inv[guid]
            entries.append(
                IfcModelDiffEntry(
                    kind="removed",
                    guid=guid,
                    ifc_type=el.is_a(),
                    attribute=None,
                    old_value=_as_str(getattr(el, "Name", None)),
                    new_value=None,
                    severity="critical",
                )
            )
        for guid in sorted(set(new_inv) - set(old_inv)):
            el = new_inv[guid]
            entries.append(
                IfcModelDiffEntry(
                    kind="added",
                    guid=guid,
                    ifc_type=el.is_a(),
                    attribute=None,
                    old_value=None,
                    new_value=_as_str(getattr(el, "Name", None)),
                    severity="warning",
                )
            )
        for guid in sorted(set(old_inv) & set(new_inv)):
            old_el = old_inv[guid]
            new_el = new_inv[guid]
            for attr in _COMPARE_ATTRS:
                if not hasattr(old_el, attr) and not hasattr(new_el, attr):
                    continue
                old_v = _as_str(getattr(old_el, attr, None))
                new_v = _as_str(getattr(new_el, attr, None))
                if old_v != new_v:
                    entries.append(
                        IfcModelDiffEntry(
                            kind="attribute_changed",
                            guid=guid,
                            ifc_type=new_el.is_a(),
                            attribute=attr,
                            old_value=old_v,
                            new_value=new_v,
                            severity="info",
                        )
                    )

        return IfcModelDiffResult(
            old_path=str(Path(old_ifc).resolve()),
            new_path=str(Path(new_ifc).resolve()),
            entries=tuple(entries),
        )
