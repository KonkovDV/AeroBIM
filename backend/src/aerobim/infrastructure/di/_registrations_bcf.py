from __future__ import annotations

from aerobim.application.use_cases.push_report_to_bcf_api import PushReportToBcfApiUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.di._di_factories import (
    _build_bcf_api_client,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.BCF_API_CLIENT,
        lambda current: _build_bcf_api_client(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.PUSH_REPORT_TO_BCF_API_USE_CASE,
        lambda current: PushReportToBcfApiUseCase(
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            bcf_api_client=current.resolve(Tokens.BCF_API_CLIENT),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
