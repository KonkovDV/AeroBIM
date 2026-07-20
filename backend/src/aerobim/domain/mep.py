"""MEP system-aware clash domain (MEP-CLASH-001 / RT-003) — engineering foundation.

Do not claim Solibri/Navisworks replacement. Default DI remains
``UnconfiguredMepSystemGraphProvider`` (fail-closed → NOT_VERIFIED / BLOCKED under
``require_mep``). Synthetic providers are unit-test only and never grant OK capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

MepExceptionKind = Literal[
    "sleeve",
    "insulation",
    "same_system",
    "intentional_containment",
]

MepIntersectionVerdict = Literal["allowed", "forbidden", "unclassified"]


class MepClearanceClass(StrEnum):
    HARD = "hard"
    SOFT = "soft"
    ADVISORY = "advisory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MepSystem:
    """Named MEP system with discipline and provenance."""

    system_id: str
    system_type: str
    discipline: str
    source_ifc: str | None = None
    element_guids: tuple[str, ...] = ()
    priority: int = 0


@dataclass(frozen=True)
class MepSystemNode:
    """Legacy graph node; prefer ``MepSystem`` for new call sites."""

    system_id: str
    system_type: str
    element_guids: tuple[str, ...]
    discipline: str = "MEP"
    source_ifc: str | None = None


@dataclass(frozen=True)
class MepSystemGraph:
    """Connectivity graph derived from IFC system assignments."""

    nodes: tuple[MepSystemNode, ...]
    edges: tuple[tuple[str, str], ...]
    """Undirected pairs of system_id connected via shared elements / ports."""
    source_ifc: str | None = None
    synthetic: bool = False
    """True when built by a synthetic/@sota-stub provider — never product evidence."""


@dataclass(frozen=True)
class MepClearanceRule:
    """Single allowed/forbidden intersection row with clearance semantics."""

    system_a: str
    system_b: str
    allowed_intersection: bool
    clearance_class: MepClearanceClass = MepClearanceClass.UNKNOWN
    min_clearance_m: float | None = None
    priority: int = 0
    exception_kinds: tuple[MepExceptionKind, ...] = ()
    notes: str | None = None
    discipline_a: str | None = None
    discipline_b: str | None = None
    system_type_a: str | None = None
    system_type_b: str | None = None


@dataclass(frozen=True)
class MepClashMatrix:
    """Customer or template clearance / intersection matrix."""

    rules: tuple[MepClearanceRule, ...]
    scope_memo_ref: str | None = None
    units: str = "m"
    default_clearance_m: float | None = None
    claim_boundary: str | None = None
    synthetic: bool = False


@dataclass(frozen=True)
class AllowedIntersectionRule:
    """Back-compat alias shape used by earlier scaffolds."""

    system_a: str
    system_b: str
    allowed: bool
    min_clearance_m: float | None = None
    requires_insulation_gap: bool = False
    notes: str | None = None


@dataclass(frozen=True)
class AllowedIntersectionMatrix:
    rules: tuple[AllowedIntersectionRule, ...]


@dataclass(frozen=True)
class MepClashFinding:
    """System-aware clash finding with full provenance (never empty-as-OK)."""

    finding_id: str
    system_a: str
    system_b: str
    verdict: MepIntersectionVerdict
    message: str
    discipline_a: str | None = None
    discipline_b: str | None = None
    system_type_a: str | None = None
    system_type_b: str | None = None
    source_ifc: str | None = None
    element_guid_a: str | None = None
    element_guid_b: str | None = None
    clearance_class: MepClearanceClass = MepClearanceClass.UNKNOWN
    allowed_intersection: bool | None = None
    priority: int = 0
    exception_kinds: tuple[MepExceptionKind, ...] = ()
    min_clearance_m: float | None = None
    capability_hint: Literal["error", "not_verified", "info"] = "error"


def _pair_key(system_a: str, system_b: str) -> tuple[str, str]:
    left, right = sorted((system_a.strip(), system_b.strip()), key=str.casefold)
    return left, right


def lookup_clearance_rule(
    matrix: MepClashMatrix,
    system_a: str,
    system_b: str,
) -> MepClearanceRule | None:
    key = _pair_key(system_a, system_b)
    for rule in matrix.rules:
        if _pair_key(rule.system_a, rule.system_b) == key:
            return rule
    return None


def evaluate_system_pair(
    *,
    system_a: MepSystem | MepSystemNode,
    system_b: MepSystem | MepSystemNode,
    matrix: MepClashMatrix,
    source_ifc: str | None = None,
    intersecting: bool = True,
) -> MepClashFinding | None:
    """Evaluate one system pair against the clearance matrix.

    - allowed intersection → no finding (``None``)
    - forbidden intersection → finding with provenance (capability_hint=error)
    - unclassified pair → NOT_VERIFIED-shaped finding (never confident ERROR)
    """

    if not intersecting:
        return None

    a_id = system_a.system_id
    b_id = system_b.system_id
    if a_id == b_id:
        return None

    discipline_a = getattr(system_a, "discipline", None)
    discipline_b = getattr(system_b, "discipline", None)
    type_a = system_a.system_type
    type_b = system_b.system_type
    guids_a = getattr(system_a, "element_guids", ())
    guids_b = getattr(system_b, "element_guids", ())
    ifc = source_ifc or getattr(system_a, "source_ifc", None) or matrix.scope_memo_ref

    rule = lookup_clearance_rule(matrix, a_id, b_id)
    if rule is None:
        return MepClashFinding(
            finding_id=f"mep-unclassified-{a_id}-{b_id}",
            system_a=a_id,
            system_b=b_id,
            verdict="unclassified",
            message=(
                f"System pair {a_id!r}↔{b_id!r} has no matrix row — "
                "NOT_VERIFIED (not a confident ERROR); RT-003 open"
            ),
            discipline_a=discipline_a,
            discipline_b=discipline_b,
            system_type_a=type_a,
            system_type_b=type_b,
            source_ifc=ifc,
            element_guid_a=guids_a[0] if guids_a else None,
            element_guid_b=guids_b[0] if guids_b else None,
            clearance_class=MepClearanceClass.UNKNOWN,
            allowed_intersection=None,
            priority=0,
            capability_hint="not_verified",
        )

    if rule.allowed_intersection:
        return None

    return MepClashFinding(
        finding_id=f"mep-forbidden-{a_id}-{b_id}",
        system_a=a_id,
        system_b=b_id,
        verdict="forbidden",
        message=(
            f"Forbidden intersection {a_id!r}↔{b_id!r} "
            f"(clearance_class={rule.clearance_class.value}; "
            f"priority={rule.priority})"
        ),
        discipline_a=discipline_a or rule.discipline_a,
        discipline_b=discipline_b or rule.discipline_b,
        system_type_a=type_a or rule.system_type_a,
        system_type_b=type_b or rule.system_type_b,
        source_ifc=ifc,
        element_guid_a=guids_a[0] if guids_a else None,
        element_guid_b=guids_b[0] if guids_b else None,
        clearance_class=rule.clearance_class,
        allowed_intersection=False,
        priority=rule.priority,
        exception_kinds=rule.exception_kinds,
        min_clearance_m=rule.min_clearance_m,
        capability_hint="error",
    )


def evaluate_matrix_against_graph(
    graph: MepSystemGraph,
    matrix: MepClashMatrix,
    *,
    intersecting_pairs: set[tuple[str, str]] | None = None,
) -> tuple[MepClashFinding, ...]:
    """Evaluate all undirected system pairs (edges or cartesian of nodes).

    When ``intersecting_pairs`` is provided, only those pairs are treated as
    geometrically intersecting; others are skipped (no finding).
    """

    nodes = {node.system_id: node for node in graph.nodes}
    if intersecting_pairs is not None:
        pairs = {_pair_key(a, b) for a, b in intersecting_pairs}
    elif graph.edges:
        pairs = {_pair_key(a, b) for a, b in graph.edges}
    else:
        ids = sorted(nodes)
        pairs = {_pair_key(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))}

    findings: list[MepClashFinding] = []
    for left, right in sorted(pairs):
        node_a = nodes.get(left)
        node_b = nodes.get(right)
        if node_a is None or node_b is None:
            findings.append(
                MepClashFinding(
                    finding_id=f"mep-missing-node-{left}-{right}",
                    system_a=left,
                    system_b=right,
                    verdict="unclassified",
                    message="Pair references unknown system node — NOT_VERIFIED",
                    source_ifc=graph.source_ifc,
                    capability_hint="not_verified",
                )
            )
            continue
        finding = evaluate_system_pair(
            system_a=node_a,
            system_b=node_b,
            matrix=matrix,
            source_ifc=graph.source_ifc,
            intersecting=True,
        )
        if finding is not None:
            findings.append(finding)
    return tuple(findings)


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


class SyntheticMepSystemGraphProvider:
    """Unit-test / scaffold name-pair graph — never product OK capability.

    /** @sota-stub */
    Tagged synthetic: returns a fixed multi-system graph independent of IFC bytes.
    Analyze path must keep ``mep_system_clash=NOT_VERIFIED`` even when nodes exist.
    """

    def __init__(
        self,
        *,
        systems: tuple[MepSystemNode, ...] | None = None,
        edges: tuple[tuple[str, str], ...] | None = None,
    ) -> None:
        self._systems = systems or (
            MepSystemNode(
                system_id="HVAC-SUPPLY",
                system_type="HVAC",
                discipline="OV",
                element_guids=("guid-hvac-1",),
                source_ifc="synthetic",
            ),
            MepSystemNode(
                system_id="SPRINKLER",
                system_type="FIRE",
                discipline="PT",
                element_guids=("guid-spk-1",),
                source_ifc="synthetic",
            ),
            MepSystemNode(
                system_id="CABLE-TRAY",
                system_type="EL",
                discipline="EL",
                element_guids=("guid-el-1",),
                source_ifc="synthetic",
            ),
        )
        self._edges = edges or (
            ("HVAC-SUPPLY", "SPRINKLER"),
            ("HVAC-SUPPLY", "CABLE-TRAY"),
            ("SPRINKLER", "CABLE-TRAY"),
        )

    def build(self, ifc_path: Path) -> MepSystemGraph:
        return MepSystemGraph(
            nodes=self._systems,
            edges=self._edges,
            source_ifc=str(ifc_path),
            synthetic=True,
        )
