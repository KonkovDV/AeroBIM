"""Wave 0 soundness & security hardening tests."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.core.config.settings import Settings
from aerobim.core.security.path_jail import PathJailError, resolve_storage_path
from aerobim.domain.errors import ClashCapabilityError
from aerobim.domain.models import (
    CapabilityState,
    ClashResult,
    ComparisonOperator,
    ParsedRequirement,
    RequirementSource,
    RuleScope,
    Severity,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.docling_requirement_extractor import (
    StructuredRequirementExtractor,
)
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
from aerobim.infrastructure.adapters.structured_drawing_analyzer import StructuredDrawingAnalyzer
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


def _load_api_security_helpers():
    spec = importlib.util.spec_from_file_location(
        "test_api_security",
        Path(__file__).resolve().parent / "test_api_security.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class PathJailTests(unittest.TestCase):
    def test_rejects_symlink_under_storage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "secret.txt"
            target.write_text("secret", encoding="utf-8")
            link = base / "link.txt"
            try:
                link.symlink_to(target)
            except OSError as exc:
                raise unittest.SkipTest(f"symlinks unavailable: {exc}") from exc

            with self.assertRaises(PathJailError):
                resolve_storage_path("link.txt", base=base)

    def test_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            with self.assertRaises(PathJailError):
                resolve_storage_path("../outside.txt", base=base)


class AuthFailClosedSettingsTests(unittest.TestCase):
    def test_production_without_token_refuses_start(self) -> None:
        settings = Settings(
            application_name="test",
            environment="production",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=False,
            api_bearer_token=None,
        )
        with self.assertRaises(RuntimeError):
            settings.require_secure_auth()

    def test_development_without_token_allowed(self) -> None:
        settings = Settings(
            application_name="test",
            environment="development",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=True,
            api_bearer_token=None,
        )
        settings.require_secure_auth()


class IncompleteRuleVisibilityTests(unittest.TestCase):
    def test_incomplete_property_rule_emits_warning(self) -> None:
        from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator

        samples = Path(__file__).resolve().parents[2] / "samples" / "ifc"
        ifc_candidates = list(samples.glob("*.ifc")) if samples.exists() else []
        if not ifc_candidates:
            raise unittest.SkipTest("no sample IFC fixtures")

        validator = IfcOpenShellValidator()
        requirement = ParsedRequirement(
            rule_id="INCOMPLETE-001",
            ifc_entity="IfcWall",
            rule_scope=RuleScope.IFC_PROPERTY,
            property_set=None,
            property_name=None,
            operator=ComparisonOperator.EQUALS,
            expected_value="REI60",
            source="test",
            source_kind=SourceKind.STRUCTURED_TEXT,
        )
        issues = validator.validate(ifc_candidates[0], [requirement])
        self.assertTrue(
            any(
                issue.rule_id == "INCOMPLETE-001" and issue.severity is Severity.WARNING
                for issue in issues
            ),
            msg=f"expected incomplete-rule warning, got: {issues}",
        )


class ClashCapabilityAndPassPolicyTests(unittest.TestCase):
    def _build_use_case(
        self,
        *,
        clash_detector,
        clash_affects_pass: bool,
        store: InMemoryAuditStore,
    ) -> AnalyzeProjectPackageUseCase:
        return AnalyzeProjectPackageUseCase(
            requirement_extractor=StructuredRequirementExtractor(),
            narrative_rule_synthesizer=NarrativeRuleSynthesizer(),
            drawing_analyzer=StructuredDrawingAnalyzer(),
            ifc_validator=MagicMock(validate=MagicMock(return_value=[])),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
            clash_detector=clash_detector,
            clash_affects_pass=clash_affects_pass,
        )

    def _request(self, ifc_path: Path) -> ValidationRequest:
        return ValidationRequest(
            request_id="req-clash-policy",
            ifc_path=ifc_path,
            requirement_source=RequirementSource(
                text="SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        )

    def test_clash_failure_is_visible_in_capabilities(self) -> None:
        store = InMemoryAuditStore()
        detector = MagicMock()
        detector.detect.side_effect = ClashCapabilityError("failed", "geometry engine crashed")
        use_case = self._build_use_case(
            clash_detector=detector,
            clash_affects_pass=False,
            store=store,
        )
        with tempfile.TemporaryDirectory() as tmp:
            ifc_path = Path(tmp) / "model.ifc"
            ifc_path.write_text("ISO-10303-21;", encoding="utf-8")
            report = use_case.execute(self._request(ifc_path))

        self.assertIsNotNone(report.capabilities)
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.clash.status, CapabilityState.FAILED)
        self.assertTrue(any(issue.rule_id == "AEROBIM-CLASH-CAPABILITY" for issue in report.issues))
        # FAILED clash capability blocks sign-off even when clash_affects_pass is false.
        self.assertFalse(report.summary.passed)

    def test_clash_affects_pass_when_enabled(self) -> None:
        store = InMemoryAuditStore()
        detector = MagicMock()
        detector.detect.return_value = [
            ClashResult(
                element_a_guid="a",
                element_b_guid="b",
                clash_type="hard",
                distance=0.0,
                description="wall vs pipe",
            )
        ]
        use_case = self._build_use_case(
            clash_detector=detector,
            clash_affects_pass=True,
            store=store,
        )
        with tempfile.TemporaryDirectory() as tmp:
            ifc_path = Path(tmp) / "model.ifc"
            ifc_path.write_text("ISO-10303-21;", encoding="utf-8")
            report = use_case.execute(self._request(ifc_path))

        self.assertFalse(report.summary.passed)
        assert report.capabilities is not None
        self.assertEqual(report.capabilities.clash.status, CapabilityState.OK)


class ProductionAuthHttpTests(unittest.TestCase):
    def test_non_dev_without_token_returns_503(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        from aerobim.presentation.http.api import create_http_app

        helpers = _load_api_security_helpers()
        container = helpers._make_test_container(environment="production")
        client = TestClient(create_http_app(container))
        response = client.get("/v1/reports")
        self.assertEqual(response.status_code, 503)

    def test_dev_without_anonymous_flag_requires_token(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        from aerobim.presentation.http.api import create_http_app

        helpers = _load_api_security_helpers()
        container = helpers._make_test_container(
            environment="development",
            allow_anonymous_dev=False,
        )
        client = TestClient(create_http_app(container))
        response = client.get("/v1/reports")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
