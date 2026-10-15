"""AB-P0-05: anonymous API only on loopback or with external-loopback ack."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from starlette.requests import Request

from aerobim.core.config.settings import Settings
from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens
from aerobim.presentation.http.context import ApiContext


class _Logger:
    def info(self, message: str, **context: object) -> None:
        pass

    def warning(self, message: str, **context: object) -> None:
        pass

    def error(self, message: str, **context: object) -> None:
        pass

    def debug(self, message: str, **context: object) -> None:
        pass


class _NoOpUseCase:
    def execute(self, request):  # noqa: ANN001
        raise RuntimeError("not used in these tests")


class _AuditStore:
    def get(self, report_id: str):  # noqa: ANN201
        return None


def _make_ctx(storage: Path, **settings_kwargs: object) -> ApiContext:
    defaults: dict[str, object] = dict(
        application_name="aerobim-anon-test",
        environment="development",
        host="127.0.0.1",
        port=8080,
        storage_dir=storage,
        debug=True,
    )
    defaults.update(settings_kwargs)
    settings = Settings(**defaults)  # type: ignore[arg-type]
    container = Container()
    container.register(Tokens.SETTINGS, lambda _: settings)
    container.register(Tokens.LOGGER, lambda _: _Logger())
    container.register(Tokens.VALIDATE_IFC_AGAINST_IDS_USE_CASE, lambda _: _NoOpUseCase())
    container.register(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE, lambda _: _NoOpUseCase())
    container.register(Tokens.AUDIT_REPORT_STORE, lambda _: _AuditStore())
    return ApiContext(container)


def _http_request() -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("test", 80),
        }
    )


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
            with self.assertRaises(HTTPException) as exc:
                ctx.require_bearer_auth(_http_request(), None)
            self.assertEqual(exc.exception.status_code, 401)
            self.assertIn("loopback", str(exc.exception.detail).lower())

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
            principal = ctx.require_bearer_auth(_http_request(), None)
            self.assertEqual(principal.subject, "anonymous-dev")
            self.assertEqual(principal.tenant_id, "tenant-demo")


if __name__ == "__main__":
    unittest.main()
