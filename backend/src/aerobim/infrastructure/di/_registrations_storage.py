from __future__ import annotations

from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
    GetAnalyzeProjectPackageJobStatusUseCase,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.di._di_factories import (
    _build_job_store,
    _build_object_store,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.OBJECT_STORE,
        lambda current: _build_object_store(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE,
        lambda current: _build_job_store(current.resolve(Tokens.SETTINGS)),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.SUBMIT_ANALYZE_PROJECT_PACKAGE_JOB_USE_CASE,
        lambda current: SubmitAnalyzeProjectPackageJobUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.GET_ANALYZE_PROJECT_PACKAGE_JOB_STATUS_USE_CASE,
        lambda current: GetAnalyzeProjectPackageJobStatusUseCase(
            current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER,
        lambda current: AnalyzeProjectPackageJobRunner(
            analyze_use_case=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE),
            job_store=current.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE),
            logger=current.resolve(Tokens.LOGGER),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
