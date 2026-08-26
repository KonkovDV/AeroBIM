"""Federated IFC MEP system graph builder (RT-003 engineering — geometry NOT_VERIFIED)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aerobim.core.security.path_jail import resolve_repo_relative_path
from aerobim.domain.ifc_spatial_index import IfcSpatialIndex
from aerobim.domain.mep import (
    FederatedMepScope,
    MepEdgeKind,
    MepSystemGraph,
    MepSystemNode,
    load_federated_mep_scope,
)
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session


class FederatedIfcMepSystemGraphProvider:
    """Build graph from IfcSystem assignments across federated scope paths.

    Requires ``FederatedMepScope.allows_federated_graph`` (customer VERIFIED or
    ENG_FIXTURE). Capability remains NOT_VERIFIED until geometry + customer matrix.
    Edges are co-presence by default; ``IfcRelConnects*`` upgrades a pair to
    ``connects`` — still not geometric clash (IfcClash / buildingSMART practice).
    """

    def __init__(
        self,
        scope: FederatedMepScope,
        *,
        repo_root: Path | None = None,
    ) -> None:
        if not scope.allows_federated_graph:
            raise ValueError("federated MEP graph requires VERIFIED (signed) or ENG_FIXTURE scope")
        self._scope = scope
        self._repo_root = (repo_root or Path.cwd()).resolve()

    @classmethod
    def from_scope_path(
        cls,
        path: Path,
        *,
        repo_root: Path | None = None,
    ) -> FederatedIfcMepSystemGraphProvider:
        scope = load_federated_mep_scope(path)
        return cls(scope, repo_root=repo_root)

    def build(self, ifc_path: Path) -> MepSystemGraph:
        del ifc_path  # federated scope manifest is authoritative for paths
        nodes: dict[str, MepSystemNode] = {}
        edges: set[tuple[str, str]] = set()
        kind_map: dict[tuple[str, str], MepEdgeKind] = {}
        source_paths: list[str] = []

        for raw_path in self._scope.federated_ifc_paths:
            resolved = self._resolve_path(raw_path)
            if not resolved.exists():
                raise FileNotFoundError(resolved)
            session = open_ifc_session(resolved)
            source_paths.append(str(resolved))
            graph_nodes, graph_edges, edge_kinds = _nodes_and_edges_from_session(
                session.model,
                session.spatial_index,
                source_ifc=str(resolved),
            )
            for node in graph_nodes:
                existing = nodes.get(node.system_id)
                if existing is None:
                    nodes[node.system_id] = node
                else:
                    merged_guids = tuple(
                        dict.fromkeys([*existing.element_guids, *node.element_guids])
                    )
                    nodes[node.system_id] = MepSystemNode(
                        system_id=existing.system_id,
                        system_type=existing.system_type,
                        element_guids=merged_guids,
                        discipline=existing.discipline,
                        source_ifc=existing.source_ifc,
                    )
            edges.update(graph_edges)
            for pair, kind in edge_kinds.items():
                prior = kind_map.get(pair)
                if prior == "connects" or kind == "connects":
                    kind_map[pair] = "connects"
                else:
                    kind_map[pair] = kind

        if not nodes:
            raise RuntimeError(
                "federated MEP IFC set produced no IfcSystem nodes (RT-003); "
                "geometry intersection not claimed"
            )

        # Co-presence / connects edges are not geometric intersections.
        synthetic = self._scope.eng_fixture or (
            "fixture" in self._scope.claim_boundary.lower()
            or "engineering" in self._scope.claim_boundary.lower()
        )
        edge_kinds_t = tuple((a, b, kind_map.get((a, b), "co_presence")) for a, b in sorted(edges))
        return MepSystemGraph(
            nodes=tuple(nodes.values()),
            edges=tuple(sorted(edges)),
            source_ifc=",".join(source_paths),
            synthetic=synthetic,
            edge_kinds=edge_kinds_t,
        )

    def build_graph(self, ifc_path: Path) -> MepSystemGraph:
        return self.build(ifc_path)

    def _resolve_path(self, raw_path: str) -> Path:
        return resolve_repo_relative_path(raw_path, repo_root=self._repo_root)


def _nodes_from_spatial_index(
    index: IfcSpatialIndex,
    *,
    source_ifc: str,
) -> tuple[tuple[MepSystemNode, ...], set[tuple[str, str]]]:
    """Back-compat: nodes + co-presence edges only."""

    nodes, edges, _kinds = _nodes_and_edges_from_session(None, index, source_ifc=source_ifc)
    return nodes, edges


def _nodes_and_edges_from_session(
    model: Any | None,
    index: IfcSpatialIndex,
    *,
    source_ifc: str,
) -> tuple[
    tuple[MepSystemNode, ...],
    set[tuple[str, str]],
    dict[tuple[str, str], MepEdgeKind],
]:
    """Build nodes + edges with co_presence / connects provenance.

    ``connects`` upgrades pairs that share an ``IfcRelConnectsElements`` (or Ports)
    link between members — topology hint only, not Solibri/IfcClash geometry.
    """

    nodes: list[MepSystemNode] = []
    edges: set[tuple[str, str]] = set()
    kind_map: dict[tuple[str, str], MepEdgeKind] = {}
    system_ids = sorted(index.systems.keys())
    for system_id in system_ids:
        guids = index.system_members(system_id)
        sample = index.lookup(guids[0]) if guids else None
        system_type = sample.ifc_type if sample is not None else "IfcSystem"
        nodes.append(
            MepSystemNode(
                system_id=system_id,
                system_type=system_type,
                element_guids=tuple(guids),
                discipline="MEP",
                source_ifc=source_ifc,
            )
        )
    for left in system_ids:
        for right in system_ids:
            if left >= right:
                continue
            pair = (left, right)
            edges.add(pair)
            kind_map[pair] = "co_presence"

    if model is not None:
        guid_to_systems: dict[str, set[str]] = {}
        for guid, element in index.elements.items():
            if element.system_ids:
                guid_to_systems[guid] = set(element.system_ids)
        for left, right in _connects_system_pairs(model, guid_to_systems):
            if left == right:
                continue
            pair = (left, right) if left < right else (right, left)
            edges.add(pair)
            kind_map[pair] = "connects"

    return tuple(nodes), edges, kind_map


def _global_id(entity: Any) -> str | None:
    raw = getattr(entity, "GlobalId", None)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _connects_system_pairs(
    model: Any,
    guid_to_systems: dict[str, set[str]],
) -> set[tuple[str, str]]:
    """Collect undirected system pairs linked by IFC connects relationships."""

    pairs: set[tuple[str, str]] = set()

    def _add_entities(left: Any, right: Any) -> None:
        guid_a = _global_id(left)
        guid_b = _global_id(right)
        if not guid_a or not guid_b:
            return
        systems_a = guid_to_systems.get(guid_a) or set()
        systems_b = guid_to_systems.get(guid_b) or set()
        for sa in systems_a:
            for sb in systems_b:
                if sa != sb:
                    pairs.add((sa, sb) if sa < sb else (sb, sa))

    for rel_type in (
        "IfcRelConnectsElements",
        "IfcRelConnectsWithRealizingElements",
        "IfcRelConnectsPorts",
    ):
        try:
            rels = list(model.by_type(rel_type))
        except Exception:
            continue
        for rel in rels:
            relating = getattr(rel, "RelatingElement", None) or getattr(rel, "RelatingPort", None)
            related = getattr(rel, "RelatedElement", None) or getattr(rel, "RelatedPort", None)
            if relating is not None and related is not None:
                _add_entities(relating, related)
                continue
            related_objects = getattr(rel, "RelatedElements", None) or ()
            relating_obj = getattr(rel, "RelatingElement", None)
            if relating_obj is not None:
                for item in related_objects:
                    _add_entities(relating_obj, item)
    return pairs


__all__ = ["FederatedIfcMepSystemGraphProvider", "_nodes_from_spatial_index"]
