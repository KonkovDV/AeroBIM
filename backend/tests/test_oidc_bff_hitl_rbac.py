"""WP-FE-15 lab RBAC: viewer verified BFF cookie → 403; default BFF stays 501.

Not customer SSO. Hard profiles remain 501 (see test_rt_c3po_post05_bff).
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.infrastructure.auth.oidc_bff_phase3 import (
    DEFAULT_BFF_SESSION_STORE,
    sign_session_cookie,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def _phase3_kwargs(storage: Path) -> dict[str, object]:
    return {
        "application_name": "test",
        "environment": "test",
        "host": "127.0.0.1",
        "port": 8080,
        "storage_dir": storage,
        "debug": True,
        "api_bearer_token": "test-token",
        "api_tenant_id": "tenant-a",
        "enforce_object_acl": True,
        "allow_anonymous_dev": False,
        "oidc_bff_client_id": "lab-client",
        "oidc_bff_authorize_url": "https://idp.example.test/authorize",
        "oidc_bff_token_url": "https://idp.example.test/token",
        "oidc_bff_client_secret": "lab-secret",
        "oidc_bff_cookie_secret": "cookie-secret",
        "oidc_bff_redirect_uri_allowlist": ("https://app.example.test/callback",),
    }


class OidcBffHitlRbacTests(unittest.TestCase):
    def setUp(self) -> None:
        DEFAULT_BFF_SESSION_STORE.clear()
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        self._tmpdir = tempfile.TemporaryDirectory()
        self.settings = Settings(**_phase3_kwargs(Path(self._tmpdir.name)))
        self.assertTrue(self.settings.oidc_bff_phase3_ready)
        self.assertTrue(self.settings.enforce_hitl_reviewer_auth)
        self.assertTrue(self.settings.require_hitl_reviewer_roles)
        self.container = bootstrap_container(self.settings)
        self.client = TestClient(create_http_app(self.container))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        DEFAULT_BFF_SESSION_STORE.clear()

    def _seed_report(self, *, tenant_id: str = "tenant-a") -> str:
        settings = self.container.resolve(Tokens.SETTINGS)
        store = self.container.resolve(Tokens.AUDIT_REPORT_STORE)
        ifc_path = settings.storage_dir / "models" / "model.ifc"
        ifc_path.parent.mkdir(parents=True, exist_ok=True)
        ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
        report_id = uuid4().hex
        store.save(
            ValidationReport(
                report_id=report_id,
                request_id="bff-hitl",
                ifc_path=ifc_path,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(),
                summary=ValidationSummary(0, 0, 0, 0, True),
                tenant_id=tenant_id,
            )
        )
        return report_id

    def _bind_cookie(
        self,
        *,
        subject: str,
        roles: frozenset[str],
        tenant_id: str | None,
        identity_verified: bool,
    ) -> None:
        session = DEFAULT_BFF_SESSION_STORE.issue(
            subject=subject,
            identity_verified=identity_verified,
            roles=roles,
            tenant_id=tenant_id,
        )
        packed = sign_session_cookie(session.session_id, "cookie-secret")
        self.client.cookies.set("aerobim_bff_session", packed)

    def test_default_discovery_without_phase3_is_501(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_bearer_token="test-token",
            )
            self.assertFalse(settings.oidc_bff_phase3_ready)
            from fastapi.testclient import TestClient

            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.get("/v1/auth/bff")
            self.assertEqual(response.status_code, 501)
            self.assertEqual(response.json()["status"], "NOT_IMPLEMENTED")

    def test_unverified_cookie_cannot_read_capabilities(self) -> None:
        self._bind_cookie(
            subject="lab-user",
            roles=frozenset({"reviewer"}),
            tenant_id="tenant-a",
            identity_verified=False,
        )
        response = self.client.get("/v1/system/capabilities")
        self.assertEqual(response.status_code, 401)

    def test_verified_cookie_without_tenant_cannot_authorize(self) -> None:
        self._bind_cookie(
            subject="lab-user",
            roles=frozenset({"reviewer"}),
            tenant_id=None,
            identity_verified=True,
        )
        response = self.client.get("/v1/system/capabilities")
        self.assertEqual(response.status_code, 401)

    def test_viewer_verified_cookie_cannot_append_expert_hitl(self) -> None:
        report_id = self._seed_report()
        self._bind_cookie(
            subject="viewer-1",
            roles=frozenset({"user"}),
            tenant_id="tenant-a",
            identity_verified=True,
        )
        accepted = self.client.post(
            f"/v1/reports/{report_id}/review-events",
            json={"event_type": "accepted", "finding_id": "f-1", "note": "no"},
        )
        self.assertEqual(accepted.status_code, 403, accepted.text)
        rejected = self.client.post(
            f"/v1/reports/{report_id}/review-events",
            json={"event_type": "rejected", "finding_id": "f-1", "note": "no"},
        )
        self.assertEqual(rejected.status_code, 403, rejected.text)
        edited = self.client.post(
            f"/v1/reports/{report_id}/review-events",
            json={"event_type": "edited_remark", "finding_id": "f-1", "note": "edit"},
        )
        self.assertEqual(edited.status_code, 403, edited.text)

    def test_user_cookie_sees_foreign_report_as_404_not_403(self) -> None:
        foreign_id = self._seed_report(tenant_id="tenant-b")
        self._bind_cookie(
            subject="viewer-1",
            roles=frozenset({"user"}),
            tenant_id="tenant-a",
            identity_verified=True,
        )
        response = self.client.get(f"/v1/reports/{foreign_id}")
        self.assertEqual(response.status_code, 404, response.text)
        self.assertNotIn("403", str(response.status_code))
        export = self.client.get(f"/v1/reports/{foreign_id}/export/html")
        self.assertEqual(export.status_code, 404, export.text)

    def test_expert_verified_cookie_can_open_then_edit_remark(self) -> None:
        report_id = self._seed_report()
        self._bind_cookie(
            subject="expert-1",
            roles=frozenset({"reviewer"}),
            tenant_id="tenant-a",
            identity_verified=True,
        )
        opened = self.client.post(
            f"/v1/reports/{report_id}/review-events",
            json={"event_type": "opened", "finding_id": "f-1"},
        )
        self.assertEqual(opened.status_code, 200, opened.text)
        edited = self.client.post(
            f"/v1/reports/{report_id}/review-events",
            json={
                "event_type": "edited_remark",
                "finding_id": "f-1",
                "previous_state": "opened",
                "note": "lab expert edit",
            },
        )
        self.assertEqual(edited.status_code, 200, edited.text)
        self.assertEqual(edited.json()["event"]["event_type"], "edited_remark")

    def test_verified_cookie_does_not_claim_production_sso(self) -> None:
        self._bind_cookie(
            subject="expert-1",
            roles=frozenset({"reviewer"}),
            tenant_id="tenant-a",
            identity_verified=True,
        )
        discovery = self.client.get("/v1/auth/bff")
        self.assertEqual(discovery.status_code, 200)
        self.assertEqual(discovery.json()["status"], "LAB")
        self.assertNotEqual(discovery.json()["status"], "IMPLEMENTED")
        session = self.client.get("/v1/auth/session")
        self.assertEqual(session.status_code, 200)
        self.assertFalse(session.json()["production_sso"])
        self.assertTrue(session.json()["identity_verified"])
        capabilities = self.client.get("/v1/system/capabilities")
        self.assertEqual(capabilities.status_code, 200)


if __name__ == "__main__":
    unittest.main()
