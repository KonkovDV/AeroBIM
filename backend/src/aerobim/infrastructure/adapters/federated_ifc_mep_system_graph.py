"""Federated IFC MEP system graph builder (RT-003 engineering — geometry NOT_VERIFIED)."""

from __future__ import annotations

from pathlib import Path

from aerobim.core.security.path_jail import resolve_repo_relative_path
from aerobim.domain.ifc_spatial_index import IfcSpatialIndex
from aerobim.domain.mep import (
    FederatedMepScope,
    MepSystemGraph,
    MepSystemNode,
    load_federated_mep_scope,
)
from aerobim.infrastructure.adapters.ifc_file_open import open_ifc_session


class FederatedIfcMepSystemGraphProvider:
    """Build graph from IfcSystem assignments across federated scope paths.

    Requires ``FederatedMepScope.allows_federated_graph`` (customer VERIFIED or
    ENG_FIXTURE). Capability remains NOT_VERIFIED until geometry + customer matrix.
    """

    def __init__(
        self,
        scope: FederatedMepScope,
        *,
        repo_root: Path | None = None,
    ) -> None:
        if not scope.allows_federated_graph:
            raise ValueError(
                "federated MEP graph requires VERIFIED (signed) or ENG_FIXTURE scope"
            )
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
        source_paths: list[str] = []

        for raw_path in self._scope.federated_ifc_paths:
            resolved = self._resolve_path(raw_path)
            if not resolved.exists():
                raise FileNotFoundError(resolved)
            session = open_ifc_session(resolved)
            source_paths.append(str(resolved))
            graph_nodes, graph_edges = _nodes_from_spatial_index(
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

        if not nodes:
            raise RuntimeError(
                "federated MEP IFC set produced no IfcSystem nodes (RT-003); "
                "geometry intersection not claimed"
            )

        # Co-presence edges are not geometric intersections.
        synthetic = self._scope.eng_fixture or (
            "fixture" in self._scope.claim_boundary.lower()
            or "engineering" in self._scope.claim_boundary.lower()
        )
        return MepSystemGraph(
            nodes=tuple(nodes.values()),
            edges=tuple(sorted(edges)),
            source_ifc=",".join(source_paths),
            synthetic=synthetic,
        )

    def _resolve_path(self, raw_path: str) -> Path:
        return resolve_repo_relative_path(raw_path, repo_root=self._repo_root)


def _nodes_from_spatial_index(
    index: IfcSpatialIndex,
    *,
    source_ifc: str,
) -> tuple[tuple[MepSystemNode, ...], set[tuple[str, str]]]:
    """Build nodes + co-presence edges (NOT geometric clash pairs)."""

    nodes: list[MepSystemNode] = []
    edges: set[tuple[str, str]] = set()
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
            edges.add((left, right))
    return tuple(nodes), edges


__all__ = ["FederatedIfcMepSystemGraphProvider"]
