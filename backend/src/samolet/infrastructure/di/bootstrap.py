from __future__ import annotations

from samolet.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from samolet.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
from samolet.core.config.settings import Settings
from samolet.core.di.container import Container, Lifecycle
from samolet.core.di.tokens import Tokens
from samolet.infrastructure.adapters.docling_requirement_extractor import StructuredRequirementExtractor
from samolet.infrastructure.adapters.filesystem_audit_store import FilesystemAuditStore
from samolet.infrastructure.adapters.ifc_clash_detector import IfcClashDetector
from samolet.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
from samolet.infrastructure.adapters.ifc_tester_ids_validator import IfcTesterIdsValidator
from samolet.infrastructure.adapters.json_structured_logger import JsonStructuredLogger
from samolet.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from samolet.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from samolet.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def bootstrap_container(settings: Settings | None = None) -> Container:
    container = Container()
    runtime_settings = settings or Settings.from_env()
    runtime_settings.storage_dir.mkdir(parents=True, exist_ok=True)

    container.register(Tokens.SETTINGS, lambda _container: runtime_settings)
    container.register(
        Tokens.LOGGER,
        lambda _container: JsonStructuredLogger(name="samolet"),
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
        Tokens.IFC_VALIDATOR,
        lambda _container: IfcOpenShellValidator(),
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
            remark_generator=current.resolve(Tokens.REMARK_GENERATOR),
            audit_report_store=current.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    return container
