from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import Severity, ValidationIssue, ValidationReport, ValidationSummary


class _NullLogger:
    """Silent logger for tests — satisfies StructuredLogger protocol."""

    def info(self, message: str, **context: object) -> None:
        pass

    def warning(self, message: str, **context: object) -> None:
        pass

    def error(self, message: str, **context: object) -> None:
        pass

    def debug(self, message: str, **context: object) -> None:
        pass


def _make_test_container():
    """Build a container backed by InMemoryAuditStore for fast HTTP tests."""
    import tempfile

    from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
    from aerobim.application.use_cases.validate_ifc_against_ids import ValidateIfcAgainstIdsUseCase
    from aerobim.core.config.settings import Settings
    from aerobim.core.di.container import Container, Lifecycle
    from aerobim.core.di.tokens import Tokens
    from aerobim.infrastructure.adapters.docling_requirement_extractor import (
        StructuredRequirementExtractor,
    )
    from aerobim.infrastructure.adapters.ifc_open_shell_validator import IfcOpenShellValidator
    from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
    from aerobim.infrastructure.adapters.narrative_rule_synthesizer import NarrativeRuleSynthesizer
    from aerobim.infrastructure.adapters.structured_drawing_analyzer import (
        StructuredDrawingAnalyzer,
    )
    from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator

    tmp = tempfile.mkdtemp()
    settings = Settings(
        application_name="test",
        environment="test",
        host="127.0.0.1",
        port=8080,
        storage_dir=Path(tmp),
        debug=True,
        cors_origins=("http://localhost:3000", "http://localhost:5173"),
    )
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    store = InMemoryAuditStore()
    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _NullLogger(), lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.REQUIREMENT_EXTRACTOR,
        lambda _: StructuredRequirementExtractor(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.NARRATIVE_RULE_SYNTHESIZER,
        lambda _: NarrativeRuleSynthesizer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.DRAWING_ANALYZER,
        lambda _: StructuredDrawingAnalyzer(),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.IFC_VALIDATOR, lambda _: IfcOpenShellValidator(), lifecycle=Lifecycle.SINGLETON
    )
    container.register(Tokens.IDS_VALIDATOR, lambda _: None, lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.REMARK_GENERATOR, lambda _: TemplateRemarkGenerator(), lifecycle=Lifecycle.SINGLETON
    )
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: store, lifecycle=Lifecycle.SINGLETON)
    container.register(
        Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
        lambda c: ValidateIfcAgainstIdsUseCase(
            requirement_extractor=c.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            ifc_validator=c.resolve(Tokens.IFC_VALIDATOR),
            audit_report_store=c.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    container.register(
        Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
        lambda c: AnalyzeProjectPackageUseCase(
            requirement_extractor=c.resolve(Tokens.REQUIREMENT_EXTRACTOR),
            narrative_rule_synthesizer=c.resolve(Tokens.NARRATIVE_RULE_SYNTHESIZER),
            drawing_analyzer=c.resolve(Tokens.DRAWING_ANALYZER),
            ifc_validator=c.resolve(Tokens.IFC_VALIDATOR),
            remark_generator=c.resolve(Tokens.REMARK_GENERATOR),
            audit_report_store=c.resolve(Tokens.AUDIT_REPORT_STORE),
        ),
        lifecycle=Lifecycle.SINGLETON,
    )
    return container


def _make_seed_report() -> ValidationReport:
    return ValidationReport(
        report_id=uuid4().hex,
        request_id="req-http-test",
        ifc_path=Path("seed.ifc"),
        created_at=datetime.now(tz=UTC).isoformat(),
        requirements=(),
        issues=(
            ValidationIssue(
                rule_id="RULE-HTML-001",
                severity=Severity.ERROR,
                message='User-controlled <tag> & "quote" content',
                element_guid="seed-guid",
            ),
        ),
        summary=ValidationSummary(
            requirement_count=0,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
        ),
    )


class ApiSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_path_traversal_ifc_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "../../etc/passwd",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            },
        )
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_path_traversal_unix_style_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "../../../secret/model.ifc",
                "requirement_text": "SAM-001|IFCWALL|Pset_WallCommon|FireRating|REI60",
            },
        )
        self.assertGreaterEqual(response.status_code, 400)
        self.assertLess(response.status_code, 500)

    def test_health_returns_ok(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)
        self.assertIn("environment", data)


class ApiReportEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_list_reports_empty(self) -> None:
        response = self.client.get("/v1/reports")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reports", data)
        self.assertIn("count", data)

    def test_get_report_invalid_id_format_returns_400(self) -> None:
        response = self.client.get("/v1/reports/not-a-uuid-format")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid report ID format", response.json()["detail"])

    def test_get_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000")
        self.assertEqual(response.status_code, 404)

    def test_export_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/json")
        self.assertEqual(response.status_code, 404)

    def test_export_html_nonexistent_report_returns_404(self) -> None:
        response = self.client.get("/v1/reports/00000000000000000000000000000000/export/html")
        self.assertEqual(response.status_code, 404)


class ApiHtmlExportTests(unittest.TestCase):
    """Tests for the HTML report export endpoint."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)
        cls.store = container.resolve(Tokens.AUDIT_REPORT_STORE)

    def _seed_report(self) -> str:
        report = _make_seed_report()
        self.store.save(report)
        return report.report_id

    def test_html_export_returns_html_content_type(self) -> None:
        report_id = self._seed_report()
        html_resp = self.client.get(f"/v1/reports/{report_id}/export/html")
        self.assertEqual(html_resp.status_code, 200)
        self.assertIn("text/html", html_resp.headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", html_resp.text)
        self.assertIn("Validation Report", html_resp.text)
        self.assertIn("seed-guid", html_resp.text)

    def test_html_export_escapes_special_characters(self) -> None:
        """Ensure XSS-safe rendering of user-controlled data."""
        from aerobim.presentation.http.api import _esc

        self.assertEqual(
            _esc('<script>alert("xss")</script>'),
            "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;",
        )
        self.assertEqual(_esc("A & B"), "A &amp; B")


class ApiMalformedInputTests(unittest.TestCase):
    """Tests for malformed/edge-case API inputs."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_missing_ifc_path_rejected(self) -> None:
        response = self.client.post("/v1/validate/ifc", json={})
        self.assertEqual(response.status_code, 422)

    def test_empty_body_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            content=b"",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)

    def test_non_json_body_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)

    def test_oversized_requirement_text_rejected(self) -> None:
        response = self.client.post(
            "/v1/validate/ifc",
            json={"ifc_path": "model.ifc", "requirement_text": "x" * 60_000},
        )
        self.assertEqual(response.status_code, 422)

    def test_analyze_missing_ifc_path_rejected(self) -> None:
        response = self.client.post("/v1/analyze/project-package", json={})
        self.assertEqual(response.status_code, 422)

    def test_report_id_not_found_returns_404(self) -> None:
        import uuid

        valid_but_missing_id = uuid.uuid4().hex
        response = self.client.get(f"/v1/reports/{valid_but_missing_id}")
        self.assertEqual(response.status_code, 404)

    def test_invalid_report_id_returns_400(self) -> None:
        response = self.client.get("/v1/reports/invalid-id-xyz")
        self.assertEqual(response.status_code, 400)


class ApiAnalyzeProjectPackageIdsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        import tempfile

        from aerobim.core.config.settings import Settings
        from aerobim.core.di.container import Container, Lifecycle
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.models import (
            FindingCategory,
            Severity,
            ValidationIssue,
            ValidationReport,
            ValidationSummary,
        )
        from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore
        from aerobim.presentation.http.api import create_http_app

        class _NoOpValidateUseCase:
            def execute(self, _request):
                return ValidationReport(
                    report_id="0" * 32,
                    request_id="noop",
                    ifc_path=Path("noop.ifc"),
                    created_at="2026-04-11T00:00:00+00:00",
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=0,
                        error_count=0,
                        warning_count=0,
                        passed=True,
                    ),
                )

        class _RecordingAnalyzeUseCase:
            def __init__(self) -> None:
                self.last_request = None

            def execute(self, request):
                self.last_request = request
                return ValidationReport(
                    report_id="1" * 32,
                    request_id=request.request_id,
                    ifc_path=request.ifc_path,
                    created_at="2026-04-11T00:00:00+00:00",
                    requirements=(),
                    issues=(
                        ValidationIssue(
                            rule_id="IDS-API-001",
                            severity=Severity.WARNING,
                            message="IDS propagated through API",
                            category=FindingCategory.IDS_VALIDATION,
                        ),
                    ),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=1,
                        error_count=0,
                        warning_count=1,
                        passed=True,
                    ),
                )

        temp_dir = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp_dir.cleanup)
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(temp_dir.name),
            debug=True,
            cors_origins=("http://localhost:3000", "http://localhost:5173"),
        )
        settings.storage_dir.mkdir(parents=True, exist_ok=True)

        store = InMemoryAuditStore()
        container = Container()
        cls.analyze_use_case = _RecordingAnalyzeUseCase()
        container.register(Tokens.SETTINGS, lambda _: settings)
        container.register(Tokens.LOGGER, lambda _: _NullLogger(), lifecycle=Lifecycle.SINGLETON)
        container.register(
            Tokens.AUDIT_REPORT_STORE,
            lambda _: store,
            lifecycle=Lifecycle.SINGLETON,
        )
        container.register(
            Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE,
            lambda _: _NoOpValidateUseCase(),
            lifecycle=Lifecycle.SINGLETON,
        )
        container.register(
            Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE,
            lambda _: cls.analyze_use_case,
            lifecycle=Lifecycle.SINGLETON,
        )

        app = create_http_app(container)
        cls.client = TestClient(app)

    def test_analyze_project_package_accepts_ids_path(self) -> None:
        response = self.client.post(
            "/v1/analyze/project-package",
            json={
                "ifc_path": "models/model.ifc",
                "ids_path": "rules/project.ids",
                "requirement_text": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"]["warning_count"], 1)
        assert self.analyze_use_case.last_request is not None
        self.assertEqual(self.analyze_use_case.last_request.ids_path.name, "project.ids")
        self.assertEqual(self.analyze_use_case.last_request.ifc_path.name, "model.ifc")


if __name__ == "__main__":
    unittest.main()
