from __future__ import annotations

from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.adapters.ifc_aabb_mep_pair_filter import IfcAabbMepPairFilter
from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector
from aerobim.infrastructure.adapters.ifc_quantity_consistency_adapter import (
    IfcQuantityConsistencyAdapter,
)
from aerobim.infrastructure.adapters.scoped_mep_system_graph_provider import (
    ScopedMepSystemGraphProvider,
)
from aerobim.infrastructure.di._di_factories import (
    _build_system_clash,
    _resolve_mep_federated_scope_path,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.CLASH_DETECTOR,
        lambda current: IfcClashDetector(
            skip_tiny_elements=current.resolve(Tokens.SETTINGS).clash_skip_tiny,
            min_aabb_volume_m3=current.resolve(Tokens.SETTINGS).clash_min_aabb_volume_m3,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MEP_SYSTEM_GRAPH_PROVIDER,
        lambda current: ScopedMepSystemGraphProvider(
            scope_path=_resolve_mep_federated_scope_path(current.resolve(Tokens.SETTINGS)),
            repo_root=Path(__file__).resolve().parents[5],
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.MEP_AABB_PAIR_FILTER,
        lambda _container: IfcAabbMepPairFilter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.QUANTITY_CONSISTENCY_CHECKER,
        lambda _container: IfcQuantityConsistencyAdapter(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SYSTEM_CLASH,
        lambda current: _build_system_clash(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
