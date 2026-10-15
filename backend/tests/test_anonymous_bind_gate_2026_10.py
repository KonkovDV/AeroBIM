"""AB-P0-05: anonymous API only on loopback or with external-loopback ack."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

from aerobim.core.config.settings import Settings

from tests.test_mutation_kills_http_context import _auth, _make_ctx, _status_auth


class AnonymousBindSafeTests(unittest.TestCase):
    def _settings(self, **kwargs: object) -> Settings:
        defaults: dict[str, object] = dict(
            application_name="aerobim-anon-test",
            environment="development",
            host="127.0.0.1",
            port=8080,
            storage_dir=Path("/tmp"),
            debug=True,
            allow_anonymous_dev=True,
            anonymous_external_loopback=False,
            signoff_profile="customer_pilot_demo",
        )
        defaults.update(kwargs)
        return Settings(**defaults)  # type: ignore[arg-type]

    def test_loopback_host_ok(self) -> None:
        self._settings(host="127.0.0.1").require_anonymous_bind_safe()
        self._settings(host="localhost").require_anonymous_bind_safe()
        self._settings(host="::1").require_anonymous_bind_safe()

    def test_non_loopback_without_ack_raises(self) -> None:
        s = self._settings(host="0.0.0.0")
        with self.assertRaises(RuntimeError) as ctx:
            s.require_anonymous_bind_safe()
        self.assertIn("AEROBIM_ANONYMOUS_EXTERNAL_LOOPBACK", str(ctx.exception))

    def test_non_loopback_with_ack_ok(self) -> None:
        self._settings(
            host="0.0.0.0", anonymous_external_loopback=True
        ).require_anonymous_bind_safe()

    def test_anonymous_off_skips_gate(self) -> None:
        self._settings(allow_anonymous_dev=False, host="0.0.0.0").require_anonymous_bind_safe()

    def test_production_env_rejects_anonymous_flag(self) -> None:
        s = self._settings(environment="production", host="127.0.0.1")
        with self.assertRaises(RuntimeError):
            s.require_anonymous_bind_safe()

    def test_hard_signoff_rejects_anonymous(self) -> None:
        s = self._settings(signoff_profile="customer_pilot", host="127.0.0.1")
        with self.assertRaises(RuntimeError):
            s.require_anonymous_bind_safe()


class AnonymousHttpContextTests(unittest.TestCase):
    def test_context_refuses_non_loopback_without_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(
                Path(tmp),
                environment="development",
                allow_anonymous_dev=True,
                host="0.0.0.0",
                anonymous_external_loopback=False,
            )
            exc = _status_auth(ctx, None)
            self.assertEqual(exc.status_code, 401)
            self.assertIn("loopback", str(exc.detail).lower())

    def test_context_allows_with_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _make_ctx(
                Path(tmp),
                environment="development",
                allow_anonymous_dev=True,
                host="0.0.0.0",
                anonymous_external_loopback=True,
                api_tenant_id="tenant-demo",
            )
            principal = _auth(ctx, None)
            self.assertEqual(principal.subject, "anonymous-dev")
            self.assertEqual(principal.tenant_id, "tenant-demo")


if __name__ == "__main__":
    unittest.main()
