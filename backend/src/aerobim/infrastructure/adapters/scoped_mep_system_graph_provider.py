"""Scope-aware MEP graph provider — VERIFIED federated scope or fail-closed."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.mep import (
    FederatedMepScope,
    MepSystemGraph,
    UnconfiguredMepSystemGraphProvider,
    load_federated_mep_scope,
)
from aerobim.infrastructure.adapters.federated_ifc_mep_system_graph import (
    FederatedIfcMepSystemGraphProvider,
)


class ScopedMepSystemGraphProvider:
    """Select federated builder only when customer scope manifest is VERIFIED."""

    def __init__(
        self,
        *,
        scope_path: Path | None,
        repo_root: Path,
        fallback: UnconfiguredMepSystemGraphProvider | None = None,
    ) -> None:
        self._scope_path = scope_path
        self._repo_root = repo_root.resolve()
        self._fallback = fallback or UnconfiguredMepSystemGraphProvider()
        self._scope: FederatedMepScope | None = None
        if scope_path is not None and scope_path.exists():
            self._scope = load_federated_mep_scope(scope_path)

    def build(self, ifc_path: Path) -> MepSystemGraph:
        if self._scope is not None and self._scope.allows_federated_graph:
            provider = FederatedIfcMepSystemGraphProvider(self._scope, repo_root=self._repo_root)
            return provider.build(ifc_path)
        return self._fallback.build(ifc_path)


__all__ = ["ScopedMepSystemGraphProvider"]
