"""POST-05: Phase 3 OIDC BFF stays lab-only; hard profiles boot-fail and keep 501."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


def _phase3_kwargs(storage: Path, *, signoff_profile: str) -> dict[str, object]:
    return {
        "application_name": "test",
        "environment": "test",
        "host": "127.0.0.1",
        "port": 8080,
        "storage_dir": storage,
        "debug": True,
        "api_bearer_token": "test-token",
        "signoff_profile": signoff_profile,
        "oidc_bff_client_id": "lab-client",
        "oidc_bff_authorize_url": "https://idp.example.test/authorize",
        "oidc_bff_token_url": "https://idp.example.test/token",
        "oidc_bff_client_secret": "lab-secret",
        "oidc_bff_cookie_secret": "cookie-secret",
        "oidc_bff_redirect_uri_allowlist": ("https://app.example.test/callback",),
    }


class Post05Phase3LabOnlyTests(unittest.TestCase):
    def test_hard_profile_never_reports_phase3_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for profile in ("samolet_pilot", "production"):
                settings = Settings(**_phase3_kwargs(Path(tmp), signoff_profile=profile))
                self.assertTrue(settings.oidc_bff_phase3_credentials_configured())
                self.assertFalse(settings.oidc_bff_phase3_ready)

    def test_lab_profile_still_ready_when_credentials_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(**_phase3_kwargs(Path(tmp), signoff_profile="development"))
            self.assertTrue(settings.oidc_bff_phase3_ready)

    def test_from_env_rejects_phase3_secrets_on_hard_profile(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot",
            "AEROBIM_ALLOW_ANONYMOUS_DEV": "true",
            "AEROBIM_OIDC_BFF_CLIENT_ID": "lab-client",
            "AEROBIM_OIDC_BFF_AUTHORIZE_URL": "https://idp.example.test/authorize",
            "AEROBIM_OIDC_BFF_TOKEN_URL": "https://idp.example.test/token",
            "AEROBIM_OIDC_BFF_CLIENT_SECRET": "lab-secret",
            "AEROBIM_OIDC_BFF_COOKIE_SECRET": "cookie-secret",
            "AEROBIM_OIDC_BFF_REDIRECT_URI_ALLOWLIST": "https://app.example.test/callback",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaisesRegex(RuntimeError, "POST-05"):
                Settings.from_env()

    def test_hard_profile_bff_discovery_stays_501(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(**_phase3_kwargs(Path(tmp), signoff_profile="production"))
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.get("/v1/auth/bff")
            self.assertEqual(response.status_code, 501)
            self.assertEqual(response.json()["status"], "NOT_IMPLEMENTED")


class ProductionComposeIsNotSsoTests(unittest.TestCase):
    def test_lan_compose_does_not_enable_phase3_bff(self) -> None:
        root = Path(__file__).resolve().parents[2]
        text = (root / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertNotIn("AEROBIM_OIDC_BFF_CLIENT_ID", text)
        self.assertNotIn("AEROBIM_OIDC_BFF_TOKEN_URL", text)
        self.assertNotIn("AEROBIM_OIDC_BFF_CLIENT_SECRET", text)
        self.assertIn("not production OIDC BFF", text)


if __name__ == "__main__":
    unittest.main()
