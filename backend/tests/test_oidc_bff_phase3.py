"""POST-05 OIDC BFF Phase 3 lab path — mock IdP token exchange."""

from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.auth.oidc_bff_phase3 import (
    DEFAULT_BFF_SESSION_STORE,
    decode_jwt_payload_unverified,
    exchange_authorization_code,
    session_from_token_payload,
)
from aerobim.infrastructure.auth.oidc_bff_stubs import DEFAULT_BFF_STATE_STORE
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def _unsigned_jwt(payload: dict[str, object]) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode("ascii").rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"{header}.{body}.sig"


class OidcBffPhase3Tests(unittest.TestCase):
    def setUp(self) -> None:
        DEFAULT_BFF_STATE_STORE.clear()
        DEFAULT_BFF_SESSION_STORE.clear()
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        self._tmpdir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            application_name="test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path(self._tmpdir.name),
            debug=True,
            api_bearer_token="test-token",
            oidc_bff_client_id="lab-client",
            oidc_bff_authorize_url="https://idp.example.test/authorize",
            oidc_bff_token_url="https://idp.example.test/token",
            oidc_bff_client_secret="lab-secret",
            oidc_bff_cookie_secret="cookie-secret",
            oidc_bff_redirect_uri_allowlist=("https://app.example.test/callback",),
        )
        self.assertTrue(self.settings.oidc_bff_phase3_ready)
        container = bootstrap_container(self.settings)
        self.client = TestClient(create_http_app(container))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()
        DEFAULT_BFF_STATE_STORE.clear()
        DEFAULT_BFF_SESSION_STORE.clear()

    def test_bff_discovery_is_lab_when_phase3_ready(self) -> None:
        response = self.client.get("/v1/auth/bff")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "LAB")

    def test_login_returns_idp_redirect(self) -> None:
        response = self.client.get(
            "/v1/auth/login",
            params={"redirect_uri": "https://app.example.test/callback"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["phase"], 3)
        self.assertTrue(body["idp_redirect_url"])
        self.assertIn("state=", body["idp_redirect_url"])

    def test_callback_issues_httponly_cookie(self) -> None:
        login = self.client.get(
            "/v1/auth/login",
            params={"redirect_uri": "https://app.example.test/callback"},
        )
        state = login.json()["state"]
        id_token = _unsigned_jwt({"sub": "user-1", "email": "a@example.test"})
        with patch(
            "aerobim.presentation.http.routes.system.exchange_authorization_code",
            return_value={"id_token": id_token, "access_token": "tok"},
        ):
            response = self.client.get(
                "/v1/auth/callback",
                params={"state": state, "code": "auth-code"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["session_cookie_issued"])
        self.assertTrue(response.cookies.get("aerobim_bff_session"))
        session = self.client.get("/v1/auth/session")
        self.assertEqual(session.status_code, 200)
        self.assertEqual(session.json()["sub"], "user-1")
        self.assertIsNone(session.json()["access_token"])
        self.assertFalse(session.json()["identity_verified"])

    def test_logout_clears_session(self) -> None:
        login = self.client.get(
            "/v1/auth/login",
            params={"redirect_uri": "https://app.example.test/callback"},
        )
        state = login.json()["state"]
        id_token = _unsigned_jwt({"sub": "user-1"})
        with patch(
            "aerobim.presentation.http.routes.system.exchange_authorization_code",
            return_value={"id_token": id_token},
        ):
            self.client.get("/v1/auth/callback", params={"state": state, "code": "c"})
        logout = self.client.post("/v1/auth/logout")
        self.assertEqual(logout.status_code, 200)
        self.assertTrue(logout.json()["session_cookie_cleared"])
        session = self.client.get("/v1/auth/session")
        self.assertEqual(session.status_code, 401)

    def test_jwt_payload_helper(self) -> None:
        token = _unsigned_jwt({"sub": "abc"})
        self.assertEqual(decode_jwt_payload_unverified(token)["sub"], "abc")
        subject, _email, verified = session_from_token_payload({"id_token": token})
        self.assertEqual(subject, "abc")
        self.assertFalse(verified)

    def test_callback_rejects_redirect_uri_off_allowlist(self) -> None:
        login = self.client.get(
            "/v1/auth/login",
            params={"redirect_uri": "https://evil.example.test/callback"},
        )
        state = login.json()["state"]
        with patch(
            "aerobim.presentation.http.routes.system.exchange_authorization_code",
            return_value={"id_token": _unsigned_jwt({"sub": "user-1"})},
        ) as exchange:
            response = self.client.get(
                "/v1/auth/callback",
                params={"state": state, "code": "auth-code"},
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_redirect_uri")
        exchange.assert_not_called()

    def test_verified_validator_rejects_unsigned_id_token(self) -> None:
        from aerobim.infrastructure.security.oidc_token_validator import (
            OidcTokenValidator,
            OidcValidationError,
        )

        class _RejectingValidator(OidcTokenValidator):
            def validate(self, token: str) -> dict[str, object]:  # noqa: ARG002
                raise OidcValidationError("unsigned lab token")

        validator = _RejectingValidator(
            issuer="https://idp.example.test",
            audience="lab-client",
            jwks_url="https://idp.example.test/jwks",
        )
        token = _unsigned_jwt({"sub": "abc"})
        with self.assertRaises(OidcValidationError):
            session_from_token_payload({"id_token": token}, validator=validator)

    def test_token_exchange_rejects_loopback_ssrf(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "SSRF"):
            exchange_authorization_code(
                token_url="https://127.0.0.1/token",
                client_id="lab-client",
                client_secret="lab-secret",
                code="auth-code",
                redirect_uri="https://app.example.test/callback",
                code_verifier="verifier",
            )

    def test_from_env_rejects_loopback_bff_token_url(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_ALLOW_ANONYMOUS_DEV": "true",
            "AEROBIM_OIDC_BFF_TOKEN_URL": "https://127.0.0.1/token",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "AEROBIM_OIDC_BFF_TOKEN_URL"):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
