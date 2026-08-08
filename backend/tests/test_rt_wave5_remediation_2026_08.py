"""Red Team Wave 5 remediation — August 2026."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from aerobim.domain.object_acl import AuthPrincipal, principal_may_edit_norm_pack
from aerobim.presentation.http.context import _oidc_tenant_from_claim


class OidcTenantClaimTests(unittest.TestCase):
    def test_string_claim_accepted(self) -> None:
        self.assertEqual(_oidc_tenant_from_claim("  t1  "), "t1")

    def test_non_string_claim_rejected(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            _oidc_tenant_from_claim({"id": "t1"})
        self.assertEqual(ctx.exception.status_code, 401)


class NormPackRbacTests(unittest.TestCase):
    def test_viewer_cannot_edit_norm_pack_in_production(self) -> None:
        principal = AuthPrincipal(
            tenant_id="t1",
            subject="user-1",
            roles=frozenset({"viewer"}),
        )
        self.assertFalse(
            principal_may_edit_norm_pack(
                enforce_rbac=True,
                principal=principal,
            )
        )

    def test_norm_editor_can_edit_norm_pack(self) -> None:
        principal = AuthPrincipal(
            tenant_id="t1",
            subject="user-1",
            roles=frozenset({"norm_editor"}),
        )
        self.assertTrue(
            principal_may_edit_norm_pack(
                enforce_rbac=True,
                principal=principal,
            )
        )


class CommitSignatureGateTests(unittest.TestCase):
    def test_missing_policy_fails_closed(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts/verify_commit_signatures.py"
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            proc = subprocess.run(
                [sys.executable, str(script), "--policy", str(missing)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("policy file not found", proc.stderr)


class RateLimitKeyHygieneTests(unittest.TestCase):
    def test_rate_limit_key_uses_hash_not_bearer_prefix(self) -> None:
        from aerobim.presentation.http.rate_limit import add_rate_limit_middleware

        captured: dict[str, object] = {}

        class _Backend:
            def allow(
                self,
                *,
                bucket: str,
                key: str,
                max_events: int,
                window_seconds: float,
            ) -> bool:
                captured["key"] = key
                return True

        with patch(
            "aerobim.presentation.http.rate_limit.build_rate_limit_backend",
            return_value=_Backend(),
        ):
            from fastapi import FastAPI
            from starlette.testclient import TestClient

            app = FastAPI()
            add_rate_limit_middleware(app, requests_per_minute=10)
            client = TestClient(app)

            @app.post("/v1/analyze/project-package/submit")
            def _noop() -> dict[str, str]:
                return {"ok": "1"}

            secret = "Bearer super-secret-jwt-token-value"
            client.post(
                "/v1/analyze/project-package/submit",
                headers={"Authorization": secret},
            )
            key = str(captured.get("key", ""))
            self.assertNotIn("super-secret", key)
            self.assertIn(":", key)


class RedisRateLimitFailClosedTests(unittest.TestCase):
    def test_production_profile_raises_when_redis_unavailable(self) -> None:
        from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend

        with patch(
            "aerobim.infrastructure.security.redis_rate_limiter.RedisRateLimitBackend",
            side_effect=RuntimeError("redis down"),
        ):
            with self.assertRaises(RuntimeError):
                build_rate_limit_backend(
                    "redis://localhost:6379/0",
                    signoff_profile="production",
                )

    def test_development_profile_falls_back(self) -> None:
        from aerobim.core.security.rate_limit_backend import InProcessRateLimitBackend
        from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend

        with patch(
            "aerobim.infrastructure.security.redis_rate_limiter.RedisRateLimitBackend",
            side_effect=RuntimeError("redis down"),
        ):
            backend = build_rate_limit_backend(
                "redis://localhost:6379/0",
                signoff_profile="development",
            )
            self.assertIsInstance(backend, InProcessRateLimitBackend)


class RuffInventoryDriftTests(unittest.TestCase):
    def test_inventory_matches_pyproject(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts/verify_ruff_s_band_inventory.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr or proc.stdout)
