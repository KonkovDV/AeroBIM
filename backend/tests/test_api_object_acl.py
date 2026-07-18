"""API-level object ACL: cross-tenant denial before artifact/export access."""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class ApiObjectAclTests(unittest.TestCase):
    def _client(self, *, storage: Path, token: str = "secret-token", tenant: str = "tenant-a"):
        from fastapi.testclient import TestClient

        settings = Settings(
            application_name="aerobim-acl-test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=storage,
            debug=True,
            api_bearer_token=token,
            api_tenant_id=tenant,
            enforce_object_acl=True,
            allow_anonymous_dev=False,
        )
        container = bootstrap_container(settings)
        return TestClient(create_http_app(container)), container

    def _seed_report(self, container, *, tenant_id: str, ifc_name: str = "model.ifc") -> str:
        settings = container.resolve(Tokens.SETTINGS)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        ifc_path = settings.storage_dir / "models" / ifc_name
        ifc_path.parent.mkdir(parents=True, exist_ok=True)
        ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
        report_id = uuid4().hex
        report = ValidationReport(
            report_id=report_id,
            request_id="acl-req",
            ifc_path=ifc_path,
            created_at=datetime.now(tz=UTC).isoformat(),
            requirements=(),
            issues=(),
            summary=ValidationSummary(0, 0, 0, 0, True),
            tenant_id=tenant_id,
        )
        store.save(report)
        return report_id

    def test_cross_tenant_report_get_denied(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed_report(container, tenant_id="tenant-b")
            response = client.get(
                f"/v1/reports/{report_id}",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 403, response.text)

    def test_cross_tenant_ifc_source_denied(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed_report(container, tenant_id="tenant-b")
            response = client.get(
                f"/v1/reports/{report_id}/source/ifc",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 403, response.text)

    def test_cross_tenant_bcf_export_denied(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed_report(container, tenant_id="tenant-b")
            response = client.get(
                f"/v1/reports/{report_id}/export/bcf",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 403, response.text)

    def test_cross_tenant_review_events_denied(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed_report(container, tenant_id="tenant-b")
            response = client.get(
                f"/v1/reports/{report_id}/review-events",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 403, response.text)
            response_kpi = client.get(
                f"/v1/reports/{report_id}/review-kpi",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response_kpi.status_code, 403, response_kpi.text)

    def test_same_tenant_report_allowed(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed_report(container, tenant_id="tenant-a")
            response = client.get(
                f"/v1/reports/{report_id}",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 200, response.text)


if __name__ == "__main__":
    unittest.main()
