"""POST-05 OIDC BFF Phase 2 stub routes — CSRF binding and honesty."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.auth.oidc_bff_stubs import DEFAULT_BFF_STATE_STORE
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class OidcBffStubRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        DEFAULT_BFF_STATE_STORE.clear()
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        self._tmpdir = tempfile.TemporaryDirectory()
        settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(self._tmpdir.name),
            debug=True,
            api_bearer_token="test-token",
            allow_anonymous_dev=False,
        )
        container = bootstrap_container(settings)
        self.client = TestClient(create_http_app(container))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        DEFAULT_BFF_STATE_STORE.clear()

    def test_login_issues_state_and_stays_not_implemented(self) -> None:
        response = self.client.get("/v1/auth/login")
        self.assertEqual(response.status_code, 501)
        body = response.json()
        self.assertEqual(body["status"], "NOT_IMPLEMENTED")
        self.assertTrue(body["stub"])
        self.assertIn("state", body)
        self.assertIsNone(body.get("idp_redirect_url"))

    def test_callback_rejects_invalid_csrf_state(self) -> None:
        response = self.client.get("/v1/auth/callback", params={"state": "not-issued"})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["error"], "invalid_or_missing_csrf_state")
        self.assertEqual(body["status"], "NOT_IMPLEMENTED")

    def test_callback_accepts_valid_state_without_session_cookie(self) -> None:
        login = self.client.get("/v1/auth/login")
        state = login.json()["state"]
        response = self.client.get(
            "/v1/auth/callback",
            params={"state": state, "code": "stub-code"},
        )
        self.assertEqual(response.status_code, 501)
        body = response.json()
        self.assertEqual(body["status"], "NOT_IMPLEMENTED")
        self.assertFalse(body["session_cookie_issued"])
        replay = self.client.get("/v1/auth/callback", params={"state": state})
        self.assertEqual(replay.status_code, 400)

    def test_logout_returns_honesty_stub(self) -> None:
        login = self.client.get("/v1/auth/login")
        state = login.json()["state"]
        response = self.client.post("/v1/auth/logout")
        self.assertEqual(response.status_code, 501)
        body = response.json()
        self.assertEqual(body["status"], "NOT_IMPLEMENTED")
        self.assertFalse(body["session_cookie_cleared"])
        self.assertFalse(body.get("csrf_store_cleared", True))
        # Public logout must not wipe outstanding CSRF states (anonymous DoS).
        callback = self.client.get("/v1/auth/callback", params={"state": state, "code": "x"})
        self.assertEqual(callback.status_code, 501)

    def test_bff_discovery_still_501(self) -> None:
        response = self.client.get("/v1/auth/bff")
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()["status"], "NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
