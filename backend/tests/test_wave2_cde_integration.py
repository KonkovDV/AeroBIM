"""Wave 2 — BCF API push, OIDC auth settings, ISO 19650 metadata."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.iso19650_metadata import enrich_iso19650_metadata
from aerobim.application.use_cases.push_report_to_bcf_api import PushReportToBcfApiUseCase
from aerobim.core.config.settings import Settings
from aerobim.domain.models import (
    Severity,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)
from aerobim.infrastructure.adapters.http_bcf_api_client import HttpBcfApiClient
from aerobim.infrastructure.adapters.in_memory_audit_store import InMemoryAuditStore


def _sample_report() -> ValidationReport:
    return ValidationReport(
        report_id="a" * 32,
        request_id="req-1",
        ifc_path=Path("model.ifc"),
        created_at="2026-07-10T12:00:00+00:00",
        requirements=(),
        issues=(
            ValidationIssue(
                rule_id="SAM-001",
                severity=Severity.ERROR,
                message="Fire rating missing",
                element_guid="2O2Fr$t4X7Zf8NOew3FLOH",
            ),
        ),
        summary=ValidationSummary(
            requirement_count=1,
            issue_count=1,
            error_count=1,
            warning_count=0,
            passed=False,
        ),
        project_name="Pilot Tower",
        stage="DD",
        information_container_id="IC-001",
        revision="P01",
        doc_status="Shared",
    )


class Iso19650MetadataTests(unittest.TestCase):
    def test_shared_status_maps_to_cde_state(self) -> None:
        meta = enrich_iso19650_metadata(_sample_report())
        self.assertEqual(meta["doc_status"], "Shared")
        self.assertEqual(meta["cde_state"], "Shared")
        self.assertEqual(meta["iso19650_container_state"], "Shared")
        self.assertEqual(meta["information_container_id"], "IC-001")


class HttpBcfApiClientTests(unittest.TestCase):
    def test_push_topics_posts_json_bodies(self) -> None:
        calls: list[tuple[str, dict[str, object]]] = []

        def fake_post(url, body, token, timeout):
            calls.append((url, body))
            self.assertIn(
                "/bcf/3.0/projects/11111111-1111-1111-1111-111111111111/topics",
                url,
            )
            self.assertEqual(token, "hub-token")
            return {"guid": body["guid"], "server_assigned_id": "ISSUE-1"}

        client = HttpBcfApiClient(
            base_url="https://hub.example.com/opencde",
            access_token="hub-token",
            http_post=fake_post,
        )
        result = client.push_report_topics(
            _sample_report(),
            project_id="11111111-1111-1111-1111-111111111111",
        )
        self.assertEqual(result.attempted, 1)
        self.assertEqual(result.succeeded, 1)
        self.assertEqual(result.failed, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["title"], "SAM-001")


class PushReportToBcfApiUseCaseTests(unittest.TestCase):
    def test_missing_report_raises(self) -> None:
        store = InMemoryAuditStore()
        use_case = PushReportToBcfApiUseCase(store, MagicMock())
        with self.assertRaises(LookupError):
            use_case.execute("b" * 32, project_id="11111111-1111-1111-1111-111111111111")

    def test_push_delegates_to_client(self) -> None:
        store = InMemoryAuditStore()
        report = _sample_report()
        store.save(report)
        client = MagicMock()
        client.push_report_topics.return_value = MagicMock(
            project_id="proj",
            attempted=1,
            succeeded=1,
            failed=0,
            topics=(),
        )
        use_case = PushReportToBcfApiUseCase(store, client)
        use_case.execute(report.report_id, project_id="proj")
        client.push_report_topics.assert_called_once()


class AuthSettingsOidcTests(unittest.TestCase):
    def test_production_accepts_oidc_without_static_bearer(self) -> None:
        settings = Settings(
            application_name="test",
            environment="production",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("."),
            debug=False,
            api_bearer_token=None,
            oidc_issuer="https://idp.example.com/",
            oidc_audience="aerobim-api",
            oidc_jwks_url="https://idp.example.com/.well-known/jwks.json",
        )
        settings.require_secure_auth()
        self.assertTrue(settings.oidc_enabled)

    def test_production_without_any_auth_fails(self) -> None:
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


class BcfApiPushHttpTests(unittest.TestCase):
    def test_push_endpoint_returns_503_when_unconfigured(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        import importlib.util

        from aerobim.presentation.http.api import create_http_app

        spec = importlib.util.spec_from_file_location(
            "test_api_security",
            Path(__file__).resolve().parent / "test_api_security.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(mod)

        # Build full bootstrap container with unconfigured BCF client
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
            )
            container = bootstrap_container(settings)
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            report = _sample_report()
            store.save(report)
            client = TestClient(create_http_app(container))
            response = client.post(
                f"/v1/reports/{report.report_id}/export/bcf-api/push",
                json={"project_id": "11111111-1111-1111-1111-111111111111"},
            )
            self.assertEqual(response.status_code, 503)

    def test_get_report_includes_iso19650_block(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        import importlib.util

        from aerobim.core.di.tokens import Tokens
        from aerobim.presentation.http.api import create_http_app

        spec = importlib.util.spec_from_file_location(
            "test_api_security",
            Path(__file__).resolve().parent / "test_api_security.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(mod)
        container = mod._make_test_container()
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        report = _sample_report()
        store.save(report)
        client = TestClient(create_http_app(container))
        response = client.get(f"/v1/reports/{report.report_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("iso19650", body)
        self.assertEqual(body["iso19650"]["cde_state"], "Shared")


if __name__ == "__main__":
    unittest.main()
