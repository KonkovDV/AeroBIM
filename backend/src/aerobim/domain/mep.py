"""MEP system-aware clash contracts (MEP-CLASH-001) — scaffold only until customer IFC.

Do not claim Solibri/Navisworks replacement. Runtime analyze path remains on generic
IfcClash until federated MEP pack + scope memo arrive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class MepSystemNode:
    system_id: str
    system_type: str
    element_guids: tuple[str, ...]


@dataclass(frozen=True)
class MepSystemGraph:
    """Connectivity graph derived from IFC system assignments."""

    nodes: tuple[MepSystemNode, ...]
    edges: tuple[tuple[str, str], ...]
    """Undirected pairs of system_id connected via shared elements / ports."""


@dataclass(frozen=True)
class AllowedIntersectionRule:
    system_a: str
    system_b: str
    allowed: bool
    min_clearance_m: float | None = None
    requires_insulation_gap: bool = False
    notes: str | None = None


@dataclass(frozen=True)
class AllowedIntersectionMatrix:
    rules: tuple[AllowedIntersectionRule, ...]


class MepSystemGraphProvider(Protocol):
    """Build duct/pipe/tray connectivity from IFC system assignments."""

    def build(self, ifc_path: Path) -> MepSystemGraph: ...


class UnconfiguredMepSystemGraphProvider:
    """Fail-closed placeholder until Samolet federated MEP IFC + scope memo exist."""

    def build(self, ifc_path: Path) -> MepSystemGraph:
        del ifc_path
        raise RuntimeError(
            "MEP system graph is not configured (MEP-CLASH-001): "
            "requires federated MEP IFC with systems and a signed scope memo"
        )
