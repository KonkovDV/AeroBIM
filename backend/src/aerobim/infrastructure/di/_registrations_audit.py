from __future__ import annotations

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ToleranceConfig
from aerobim.infrastructure.adapters.filesystem_review_event_store import FilesystemReviewEventStore
from aerobim.infrastructure.adapters.json_detached_signature_auditor import (
    JsonDetachedSignatureAuditor,
)
from aerobim.infrastructure.adapters.json_package_inventory_loader import (
    JsonPackageInventoryLoader,
)
from aerobim.infrastructure.adapters.json_structured_logger import JsonStructuredLogger
from aerobim.infrastructure.adapters.openrebar_evidence_verifier import OpenRebarEvidenceVerifier
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator
from aerobim.infrastructure.di._di_factories import (
    _build_audit_report_store,
)


def register_group(
    container: Container,
    runtime_settings: Settings,
    *,
    tolerance: ToleranceConfig,
) -> None:
    container.register(
        Tokens.LOGGER,
        lambda _container: JsonStructuredLogger(name="aerobim"),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DOCUMENT_SIGNATURE_AUDITOR,
        lambda _container: JsonDetachedSignatureAuditor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.PACKAGE_INVENTORY_LOADER,
        lambda _container: JsonPackageInventoryLoader(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.EXTERNAL_EVIDENCE_VERIFIER,
        lambda _container: OpenRebarEvidenceVerifier(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REMARK_GENERATOR,
        lambda current: TemplateRemarkGenerator(
            locale=current.resolve(Tokens.SETTINGS).remark_locale
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.AUDIT_REPORT_STORE,
        lambda current: _build_audit_report_store(current),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.REVIEW_EVENT_STORE,
        lambda current: FilesystemReviewEventStore(
            current.resolve(Tokens.SETTINGS).storage_dir,
            fail_closed=current.resolve(Tokens.SETTINGS).audit_fail_closed,
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
