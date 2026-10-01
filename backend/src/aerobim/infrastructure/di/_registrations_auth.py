from __future__ import annotations

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.di._di_factories import (
    _build_oidc_validator,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.OIDC_TOKEN_VALIDATOR,
        lambda current: _build_oidc_validator(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
