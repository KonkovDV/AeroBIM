"""Red Team remediation tests — compose hygiene, soft sign-off, IDS audit wiring."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.domain.models import (
    CapabilityState,
    FindingCategory,
    RequirementSource,
    Severity,
    ValidationIssue,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _minimal_uc(**kwargs: object) -> AnalyzeProjectPackageUseCase:
    base: dict[str, object] = {
        "requirement_extractor": StructuredRequirementExtractor(),
        "narrative_rule_synthesizer": NarrativeRuleSynthesizer(),
        "drawing_analyzer": StructuredDrawingAnalyzer(),
        "ifc_validator": MagicMock(validate=MagicMock(return_value=[])),
        "remark_generator": TemplateRemarkGenerator(),
        "audit_report_store": InMemoryAuditStore(),
    }
    base.update(kwargs)
    return AnalyzeProjectPackageUseCase(**base)  # type: ignore[arg-type]


class ComposeAuthHygieneTests(unittest.TestCase):
    def test_default_compose_is_not_production_with_anonymous_default(self) -> None:
        text = (_repo_root() / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertNotIn("AEROBIM_ENV: production", text)
        self.assertIn("127.0.0.1:8080:8080", text)
        self.assertIn("AEROBIM_ALLOW_ANONYMOUS_DEV: ${AEROBIM_ALLOW_ANONYMOUS_DEV:-false}", text)
        self.assertNotIn("dev-local-token-change-me", text)

    def test_production_compose_requires_bearer_secret(self) -> None:
        text = (_repo_root() / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("AEROBIM_ENV: production", text)
        self.assertIn("AEROBIM_API_BEARER_TOKEN: ${AEROBIM_API_BEARER_TOKEN:?", text)
        self.assertIn('AEROBIM_ALLOW_ANONYMOUS_DEV: "false"', text)
        self.assertNotIn("dev-local-token-change-me", text)


class SoftSignoffUnderNonDevTests(unittest.TestCase):
    def test_production_env_rejects_development_signoff_profile(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "production",
                "AEROBIM_SIGNOFF_PROFILE": "development",
                "AEROBIM_API_BEARER_TOKEN": "rt-test-token-not-for-prod",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(RuntimeError, "not allowed"):
                Settings.from_env()

    def test_from_env_defaults_anonymous_off(self) -> None:
        with patch.dict(os.environ, {"AEROBIM_ENV": "development"}, clear=False):
            os.environ.pop("AEROBIM_ALLOW_ANONYMOUS_DEV", None)
            settings = Settings.from_env()
        self.assertFalse(settings.allow_anonymous_dev)


class IdsDocumentAuditorWiringTests(unittest.TestCase):
    def test_ids_audit_issues_fail_closed_on_package(self) -> None:
        class _Auditor:
            def audit(self, ids_path: Path):  # noqa: ANN001
                del ids_path
                return [
                    ValidationIssue(
                        rule_id="AEROBIM-IDS-AUDIT",
                        severity=Severity.ERROR,
                        message="unsupported IDS facet",
                        category=FindingCategory.IFC_VALIDATION,
                        source_id="ids-audit",
                    )
                ]

        class _Ids:
            def validate(self, ids_path: Path, ifc_path: Path):  # noqa: ANN001
                del ids_path, ifc_path
                return []

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            ifc = root / "m.ifc"
            ids = root / "rules.ids"
            ifc.write_text("ISO-10303-21;", encoding="utf-8")
            ids.write_text("<ids/>", encoding="utf-8")
            uc = _minimal_uc(ids_validator=_Ids(), ids_document_auditor=_Auditor())
            report = uc.execute(
                ValidationRequest(
                    request_id="rt-ids-audit",
                    ifc_path=ifc,
                    requirement_source=RequirementSource(
                        text="R1|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
                    ),
                    ids_path=ids,
                )
            )
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.ids.status, CapabilityState.FAILED)
        self.assertFalse(report.summary.passed)


class OidcJwksGuardSurfaceTests(unittest.TestCase):
    def test_validate_uses_fetch_jwks_not_pyjwkclient_http(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "infrastructure"
            / "security"
            / "oidc_token_validator.py"
        )
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("from jwt import PyJWKClient", text)
        self.assertNotIn("PyJWKClient(", text)
        self.assertIn("fetch_jwks", text)
        self.assertIn("safe_urlopen", text)


if __name__ == "__main__":
    unittest.main()
