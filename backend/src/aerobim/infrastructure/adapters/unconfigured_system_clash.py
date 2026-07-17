"""SystemClashPort — fail-closed until federated MEP pack + clearance matrix (MEP-CLASH-001)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from aerobim.domain.tz_architecture_ports import SpatialFinding


class UnconfiguredSystemClash:
    """Honesty adapter: never returns empty-as-OK for MEP system clash."""

    def detect(
        self,
        model_path: Path,
        *,
        clearance_matrix: Mapping[tuple[str, str], float] | None = None,
    ) -> list[SpatialFinding]:
        del model_path, clearance_matrix
        raise RuntimeError(
            "MEP system-aware clash is not configured (MEP-CLASH-001): "
            "requires federated MEP IFC, system graph, and signed clearance matrix"
        )
