"""Thin IFC model revision diff (GUID add/delete + simple attribute changes).

Engineering signal for TZ matrix row 28 scaffolding — **not** multi-package CDE
compare, not «документация одобрена», does not close RT-001.
No ``deepdiff`` dependency: uses IfcOpenShell APIs already in the stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

DiffKind = Literal["added", "removed", "attribute_changed"]
DiffSeverity = Literal["critical", "warning", "info"]


@dataclass(frozen=True)
class IfcModelDiffEntry:
    kind: DiffKind
    guid: str
    ifc_type: str
    attribute: str | None
    old_value: str | None
    new_value: str | None
    severity: DiffSeverity

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "guid": self.guid,
            "ifc_type": self.ifc_type,
            "attribute": self.attribute,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class IfcModelDiffResult:
    """Package-neutral IFC↔IFC element inventory delta."""

    old_path: str
    new_path: str
    entries: tuple[IfcModelDiffEntry, ...]
    claim_level: str = "engineering_signal_only"
    closes_rt001: bool = False
    note: str = (
        "GUID add/delete + Name/ObjectType/Tag/Description attribute delta only; "
        "not CDE version management; not product accuracy"
    )

    def summary(self) -> dict[str, int]:
        counts = {"added": 0, "removed": 0, "attribute_changed": 0}
        for e in self.entries:
            counts[e.kind] = counts.get(e.kind, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "ifc-model-diff",
            "claim_level": self.claim_level,
            "closes_rt001": self.closes_rt001,
            "note": self.note,
            "old_path": self.old_path,
            "new_path": self.new_path,
            "summary": self.summary(),
            "entries": [e.to_dict() for e in self.entries],
        }


class IfcModelDiff(Protocol):
    """Compare two IFC files by GlobalId inventory + selected attributes."""

    def compare(self, old_ifc: Path, new_ifc: Path) -> IfcModelDiffResult: ...
