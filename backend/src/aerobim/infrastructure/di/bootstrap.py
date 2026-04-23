from __future__ import annotations

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
    GetAnalyzeProjectPackageJobStatusUseCase,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from aerobim.infrastructure.adapters.ifc_clash_detector import IfcClashDetector
from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from aerobim.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)
from aerobim.infrastructure.adapters.json_structured_logger import JsonStructuredLogger
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.adapters.vlm_drawing_analyzer import VlmDrawingAnalyzer


def bootstrap_container(settings: Settings | None = None) -> Container:
    container = Container()
    runtime_settings = settings or Settings.from_env()
    runtime_settings.storage_dir.mkdir(parents=True, exist_ok=True)

    container.register(Tokens.SETTINGS, lambda _container: runtime_settings)
    container.register(
        Tokens.LOGGER,
        lambda _container: JsonStructuredLogger(name="aerobim"),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REQUIREMENT_EXTRACTOR,
        lambda _container: StructuredRequirementExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NARRATIVE_RULE_SYNTHESIZER,
        lambda _container: NarrativeRuleSynthesizer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER,
        lambda _container: StructuredDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.VISION_DRAWING_ANALYZER,
        lambda _container: VlmDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    tolerance = ToleranceConfig()
    container.register(
        Tokens.IFC_VALIDATOR,
        lambda _container: IfcOpenShellValidator(tolerance=tolerance),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IDS_VALIDATOR,
        lambda _container: IfcTesterIdsValidator(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.CLASH_DETECTOR,
        lambda _container: IfcClashDetector(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REMARK_GENERATOR,
        lambda _container: TemplateRemarkGenerator(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.AUDIT_REPORT_STORE,
        lambda current: FilesystemAuditStore(current.resolve(Tokens.SETTINGS).storage_dir),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE,
        lambda current: InMemoryAnalyzeProjectPackageJobStore(
            snapshot_path=(
                current.resolve(Tokens.SETTINGS).storage_dir
                / "analyze_project_package_jobs.snapshot.json"
            )
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
        lambda current: ValidateIfcAgainstIdsUseCase(
            requirement_extractor=current.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            ifc_validator=current.resolve(Tokens.IFC_VALIDATOR),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            ids_validator=current.resolve(Tokens.IDS_VALIDATOR),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
        lambda current: AnalyzeProjectPackageUseCase(
            requirement_extractor=current.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            narrative_rule_synthesizer=current.resolve(Tokens.NARRATIVE_RULE_SYNTHESIZER),
            drawing_analyzer=current.resolve(Tokens.DRAWING_ANALYZER),
            ifc_validator=current.resolve(Tokens.IFC_VALIDATOR),
            ids_validator=current.resolve(Tokens.IDS_VALIDATOR),
            vision_drawing_analyzer=current.resolve(Tokens.VISION_DRAWING_ANALYZER),
            remark_generator=current.resolve(Tokens.REMARK_GENERATOR),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
            tolerance=tolerance,
            clash_detector=current.resolve(Tokens.CLASH_DETECTOR),
        ),
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
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    return container
