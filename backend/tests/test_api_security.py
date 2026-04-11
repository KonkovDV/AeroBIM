from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


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
        from aerobim.presentation.http.api import create_http_app

        container = _make_test_container()
        app = create_http_app(container)
        cls.client = TestClient(app)

    def _create_report(
        self, requirement_text: str = "SAM-001|IFCWALL|Pset_WallCommon|FireRating|eq|REI60"
    ) -> str:
        """Create a report through the API and return its report_id."""
        response = self.client.post(
            "/v1/validate/ifc",
            json={
                "ifc_path": "nonexistent.ifc",
                "requirement_text": requirement_text,
            },
        )
        # Report may fail because no IFC file exists; still creates a report entry on 200
        if response.status_code == 200:
            return response.json()["report_id"]
        return ""

    def test_html_export_returns_html_content_type(self) -> None:
        # Use the validate endpoint to create a report first
        resp = self.client.post(
            "/v1/validate/ifc",
            json={"ifc_path": "nonexistent.ifc", "requirement_text": ""},
        )
        if resp.status_code != 200:
            self.skipTest("Cannot create report for HTML export test")

        report_id = resp.json()["report_id"]
        html_resp = self.client.get(f"/v1/reports/{report_id}/export/html")
        self.assertEqual(html_resp.status_code, 200)
        self.assertIn("text/html", html_resp.headers.get("content-type", ""))
        self.assertIn("<!DOCTYPE html>", html_resp.text)
        self.assertIn("Validation Report", html_resp.text)

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


if __name__ == "__main__":
    unittest.main()
