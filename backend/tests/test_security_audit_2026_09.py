"""External static-audit remediations (RL-01, RL-02, OPS-01) — September 2026."""

from __future__ import annotations

import re
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import (
    ValidationReport,
    ValidationSummary,
)
from aerobim.domain.object_acl import (
    LAB_ANONYMOUS_ACTOR,
    AuthPrincipal,
    principal_may_list_unscoped_reports,
    review_actor_from_principal,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.rate_limit import (
    _RATE_LIMIT_POST_ALLOWLIST,
    add_rate_limit_middleware,
    heavy_get_path_is_rate_limited,
    post_path_is_rate_limited,
)


def _iter_http_routes(app: object) -> list[object]:
    found: list[object] = []

    def walk(routes: object) -> None:
        for route in routes:  # type: ignore[union-attr]
            inner = getattr(route, "original_router", None)
            if inner is not None:
                walk(inner.routes)
                continue
            nested = getattr(route, "routes", None)
            if nested is not None and not hasattr(route, "dependant"):
                walk(nested)
                continue
            found.append(route)

    walk(app.routes)  # type: ignore[attr-defined]
    return found


def _sample_path(route_path: str) -> str:
    return re.sub(r"\{[^}]+\}", "id", route_path)


class PreAuthRateLimitTests(unittest.TestCase):
    def test_token_spray_from_one_ip_hits_429(self) -> None:
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        app = FastAPI()
        add_rate_limit_middleware(app, requests_per_minute=100)

        @app.post("/v1/analyze/project-package")
        def _noop() -> dict[str, str]:
            return {"ok": "1"}

        client = TestClient(app)
        statuses = [
            client.post(
                "/v1/analyze/project-package",
                headers={"Authorization": f"Bearer spray-{index}"},
            ).status_code
            for index in range(200)
        ]
        self.assertIn(429, statuses)
        self.assertGreaterEqual(statuses.count(429), 1)

    def test_uploads_exact_path_is_rate_limited(self) -> None:
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        app = FastAPI()
        add_rate_limit_middleware(app, requests_per_minute=3)

        @app.post("/v1/uploads")
        def _noop() -> dict[str, str]:
            return {"ok": "1"}

        client = TestClient(app)
        codes = [client.post("/v1/uploads").status_code for _ in range(5)]
        self.assertIn(429, codes)

    def test_every_v1_post_is_limited_or_allowlisted(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
                http_rate_limit_per_minute=0,
            )
            app = create_http_app(bootstrap_container(settings))
            TestClient(app)
            missing: list[str] = []
            for route in _iter_http_routes(app):
                methods = getattr(route, "methods", None) or set()
                if "POST" not in methods:
                    continue
                path = str(getattr(route, "path", "") or "")
                if not path.startswith("/v1/"):
                    continue
                sample = _sample_path(path)
                if post_path_is_rate_limited(sample):
                    continue
                if path in _RATE_LIMIT_POST_ALLOWLIST or sample in _RATE_LIMIT_POST_ALLOWLIST:
                    continue
                missing.append(path)
            self.assertEqual(
                missing,
                [],
                "POST /v1/* must be rate-limited or listed in _RATE_LIMIT_POST_ALLOWLIST "
                "with a justification comment: " + ", ".join(missing),
            )


class ProductionComposeHardeningTests(unittest.TestCase):
    def test_ops01_compose_hardening_keys(self) -> None:
        root = Path(__file__).resolve().parents[2]
        text = (root / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("read_only: true", text)
        self.assertIn("/tmp", text)
        self.assertIn("cap_drop:", text)
        self.assertIn("ALL", text)
        self.assertIn("no-new-privileges:true", text)
        self.assertIn("pids_limit:", text)
        self.assertIn("--requirepass", text)
        self.assertIn("AEROBIM_REDIS_PASSWORD:?", text)


class FollowOnAuditFindingTests(unittest.TestCase):
    def test_f04_review_actor_never_uses_client_payload(self) -> None:
        named = AuthPrincipal(subject="expert-1", auth_scheme="oidc")
        self.assertEqual(review_actor_from_principal(named), "expert-1")
        empty = AuthPrincipal(subject=None, auth_scheme="anonymous")
        self.assertEqual(review_actor_from_principal(empty), LAB_ANONYMOUS_ACTOR)
        self.assertNotEqual(review_actor_from_principal(empty), "attacker")

    def test_f03_platform_admin_is_explicit_role(self) -> None:
        self.assertFalse(
            principal_may_list_unscoped_reports(AuthPrincipal(tenant_id=None, roles=frozenset()))
        )
        self.assertFalse(
            principal_may_list_unscoped_reports(
                AuthPrincipal(tenant_id=None, roles=frozenset({"admin"}), is_service_token=True)
            )
        )
        self.assertTrue(
            principal_may_list_unscoped_reports(
                AuthPrincipal(
                    tenant_id=None,
                    roles=frozenset({"platform_admin"}),
                    auth_scheme="oidc",
                )
            )
        )

    def test_f03_bearer_without_tenant_lists_nothing(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-f03",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                api_bearer_token="secret-token",
                api_tenant_id=None,
                enforce_object_acl=False,
                allow_anonymous_dev=False,
            )
            container = bootstrap_container(settings)
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            created = datetime.now(tz=UTC).isoformat()
            for tenant, rid in (("tenant-a", "a" * 32), ("tenant-b", "b" * 32)):
                store.save(
                    ValidationReport(
                        report_id=rid,
                        request_id=f"req-{tenant}",
                        ifc_path=Path("seed.ifc"),
                        created_at=created,
                        requirements=(),
                        issues=(),
                        summary=ValidationSummary(0, 0, 0, 0, True),
                        tenant_id=tenant,
                    )
                )
            client = TestClient(create_http_app(container))
            response = client.get(
                "/v1/reports",
                headers={"Authorization": "Bearer secret-token"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["count"], 0)
            self.assertEqual(response.json()["reports"], [])

    def test_f04_http_review_event_ignores_payload_actor(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-f04",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
            )
            container = bootstrap_container(settings)
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            report_id = "c" * 32
            store.save(
                ValidationReport(
                    report_id=report_id,
                    request_id="req-f04",
                    ifc_path=Path("seed.ifc"),
                    created_at=datetime.now(tz=UTC).isoformat(),
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(0, 0, 0, 0, True),
                    tenant_id="lab-anonymous",
                )
            )
            client = TestClient(create_http_app(container))
            response = client.post(
                f"/v1/reports/{report_id}/review-events",
                json={"event_type": "opened", "actor": "attacker"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            actor = response.json()["event"]["actor"]
            self.assertEqual(actor, "anonymous-dev")
            self.assertNotEqual(actor, "attacker")

    def test_f12_heavy_get_paths_are_classified(self) -> None:
        rid = "a" * 32
        self.assertTrue(heavy_get_path_is_rate_limited(f"/v1/reports/{rid}/export/pdf"))
        self.assertTrue(heavy_get_path_is_rate_limited(f"/v1/reports/{rid}/source/ifc"))
        self.assertTrue(
            heavy_get_path_is_rate_limited(f"/v1/reports/{rid}/drawing-assets/A1/preview")
        )
        self.assertFalse(heavy_get_path_is_rate_limited("/v1/reports"))
        self.assertFalse(heavy_get_path_is_rate_limited(f"/v1/reports/{rid}"))

    def test_f12_export_get_hits_per_ip_limit(self) -> None:
        try:
            from fastapi import FastAPI
            from starlette.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        app = FastAPI()
        add_rate_limit_middleware(app, requests_per_minute=3)

        @app.get("/v1/reports/{report_id}/export/json")
        def _noop(report_id: str) -> dict[str, str]:
            return {"id": report_id}

        client = TestClient(app)
        rid = "d" * 32
        codes = [client.get(f"/v1/reports/{rid}/export/json").status_code for _ in range(5)]
        self.assertIn(429, codes)

    def test_f13_dependabot_covers_frontend_npm(self) -> None:
        root = Path(__file__).resolve().parents[2]
        text = (root / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: npm", text)
        self.assertIn('directory: "/frontend"', text)

    def test_f05_export_rejects_non_hex_report_id(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-f05",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
            )
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.get("/v1/reports/not-a-uuid/export/json")
            self.assertEqual(response.status_code, 400)


class RemainderAuditFindingTests(unittest.TestCase):
    def test_rt_f08_dial_pin_rewrites_hostname_to_ip(self) -> None:
        import socket
        from unittest.mock import patch

        from aerobim.core.security import outbound_url as outbound

        seen: list[str] = []

        def fake_conn(address: tuple[object, ...], *args: object, **kwargs: object) -> None:
            del args, kwargs
            seen.append(str(address[0]))
            raise OSError("pinned-dial")

        outbound.set_outbound_dial_pin("s3.test.invalid", "203.0.113.77")
        try:
            with patch.object(outbound, "_orig_create_connection", fake_conn):
                with self.assertRaises(OSError):
                    socket.create_connection(("s3.test.invalid", 443), timeout=0.01)
                with self.assertRaises(OSError):
                    socket.create_connection(("other.test.invalid", 443), timeout=0.01)
            self.assertEqual(seen, ["203.0.113.77", "other.test.invalid"])
        finally:
            outbound.clear_outbound_dial_pins()

    def test_rt_f08_s3_virtual_host_is_pinned(self) -> None:
        from aerobim.core.security.outbound_url import (
            PinnedOutboundUrl,
            clear_outbound_dial_pins,
            outbound_dial_pin_for,
            pin_s3_outbound_dials,
        )

        pinned = PinnedOutboundUrl(
            url="https://s3.example.test",
            hostname="s3.example.test",
            pinned_ip="203.0.113.10",
            port=443,
            scheme="https",
        )
        try:
            pin_s3_outbound_dials(pinned, bucket="bucket")
            self.assertEqual(outbound_dial_pin_for("s3.example.test"), "203.0.113.10")
            self.assertEqual(outbound_dial_pin_for("bucket.s3.example.test"), "203.0.113.10")
        finally:
            clear_outbound_dial_pins()

    def test_rt_f11_hard_profile_credentials_default_off(self) -> None:
        from aerobim.core.config.settings import _cors_allow_credentials_from_env

        self.assertFalse(
            _cors_allow_credentials_from_env(
                ("https://app.example",),
                env_name="production",
            )
        )
        self.assertTrue(
            _cors_allow_credentials_from_env(
                ("http://localhost:5173",),
                env_name="test",
            )
        )

    def test_rt_f15_known_bugs_records_license_inventory(self) -> None:
        root = Path(__file__).resolve().parents[2]
        known = (root / "KNOWN_BUGS.md").read_text(encoding="utf-8")
        self.assertIn("F-15", known)
        self.assertIn("dependency_license_inventory.json", known)
        self.assertIn("HD19-S3-02", known)
        self.assertIn("PROC-01", known)
        self.assertIn("Closed 2026-09-05", known)


if __name__ == "__main__":
    unittest.main()
