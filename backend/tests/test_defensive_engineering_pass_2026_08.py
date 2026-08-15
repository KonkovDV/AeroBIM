"""DEF-2026-08: tenant claim, ACL-before-read, durable jobs, datastore SSRF."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.core.security.outbound_url import UnsafeOutboundUrlError, assert_safe_outbound_url
from aerobim.domain.models import ValidationReport, ValidationSummary
from aerobim.infrastructure.di._di_factories import _build_job_store
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend
from aerobim.presentation.http.api import create_http_app
from aerobim.presentation.http.errors import public_not_found_detail


class ProductionDurableRuntimeTests(unittest.TestCase):
    def test_from_env_production_without_redis_fails(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "production",
                "AEROBIM_API_BEARER_TOKEN": "tok",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_REDIS_URL", None)
            os.environ.pop("AEROBIM_SIGNOFF_PROFILE", None)
            with self.assertRaisesRegex(RuntimeError, "AEROBIM_REDIS_URL"):
                Settings.from_env()

    def test_job_store_rejects_in_memory_outside_dev(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="t",
                environment="production",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=False,
                api_bearer_token="tok",
                redis_url=None,
            )
            with self.assertRaisesRegex(RuntimeError, "in-memory"):
                _build_job_store(settings)

    def test_rate_limiter_fail_closed_without_redis_url(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "AEROBIM_REDIS_URL is unset"):
            build_rate_limit_backend(None, signoff_profile="production", fail_closed=True)

    def test_from_env_production_rejects_wildcard_cors(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AEROBIM_ENV": "production",
                "AEROBIM_API_BEARER_TOKEN": "tok",
                "AEROBIM_REDIS_URL": "redis://127.0.0.1:6379/0",
                "AEROBIM_CORS_ORIGINS": "*",
            },
            clear=False,
        ):
            os.environ.pop("AEROBIM_SIGNOFF_PROFILE", None)
            with self.assertRaisesRegex(RuntimeError, "CORS"):
                Settings.from_env()


class DatastoreSsrfTests(unittest.TestCase):
    def test_http_ssrf_still_blocks_rfc1918_and_mapped_loopback(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://10.0.0.5/jwks", resolve_dns=False)
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://[::ffff:127.0.0.1]/jwks", resolve_dns=False)


class AclBeforeReadAndAntiEnumTests(unittest.TestCase):
    def _client(self, *, storage: Path, tenant: str = "tenant-a"):
        from fastapi.testclient import TestClient

        settings = Settings(
            application_name="aerobim-def-test",
            environment="test",
            host="127.0.0.1",
            port=8080,
            storage_dir=storage,
            debug=True,
            api_bearer_token="secret-token",
            api_tenant_id=tenant,
            enforce_object_acl=True,
            allow_anonymous_dev=False,
        )
        container = bootstrap_container(settings)
        return TestClient(create_http_app(container)), container

    def _seed(self, container, *, tenant_id: str) -> str:
        settings = container.resolve(Tokens.SETTINGS)
        store = container.resolve(Tokens.AUDIT_REPORT_STORE)
        ifc_path = settings.storage_dir / "models" / "model.ifc"
        ifc_path.parent.mkdir(parents=True, exist_ok=True)
        ifc_path.write_text("ISO-10303-21;\n", encoding="utf-8")
        report_id = uuid4().hex
        store.save(
            ValidationReport(
                report_id=report_id,
                request_id="def-req",
                ifc_path=ifc_path,
                created_at=datetime.now(tz=UTC).isoformat(),
                requirements=(),
                issues=(),
                summary=ValidationSummary(0, 0, 0, 0, True),
                tenant_id=tenant_id,
            )
        )
        return report_id

    def test_cross_tenant_and_missing_share_404_body(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            foreign = self._seed(container, tenant_id="tenant-b")
            missing = "a" * 32
            headers = {"Authorization": "Bearer secret-token"}
            denied = client.get(f"/v1/reports/{foreign}", headers=headers)
            absent = client.get(f"/v1/reports/{missing}", headers=headers)
            self.assertEqual(denied.status_code, 404)
            self.assertEqual(absent.status_code, 404)
            self.assertEqual(denied.json()["detail"], public_not_found_detail())
            self.assertEqual(denied.json()["detail"], absent.json()["detail"])
            self.assertNotIn(foreign, denied.text)

    def test_peek_tenant_does_not_use_tid_style_spoof(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, container = self._client(storage=Path(tmp), tenant="tenant-a")
            report_id = self._seed(container, tenant_id="tenant-a")
            store = container.resolve(Tokens.AUDIT_REPORT_STORE)
            self.assertEqual(store.peek_tenant_id(report_id), "tenant-a")
            self.assertIsNone(store.peek_tenant_id("b" * 32))
            headers = {"Authorization": "Bearer secret-token"}
            ok = client.get(f"/v1/reports/{report_id}", headers=headers)
            self.assertEqual(ok.status_code, 200, ok.text)

    def test_duplicate_authorization_headers_rejected(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, _container = self._client(storage=Path(tmp))
            response = client.get(
                "/v1/reports",
                headers=[
                    ("Authorization", "Bearer secret-token"),
                    ("Authorization", "Bearer other-token"),
                ],
            )
            self.assertEqual(response.status_code, 401, response.text)

    def test_oversized_authorization_header_rejected(self) -> None:
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        with tempfile.TemporaryDirectory() as tmp:
            client, _container = self._client(storage=Path(tmp))
            token = "Bearer " + ("x" * 9000)
            response = client.get("/v1/reports", headers={"Authorization": token})
            self.assertEqual(response.status_code, 401, response.text)


class ProductionCapabilityFailClosedTests(unittest.TestCase):
    def test_skipped_required_clash_cannot_green_pass(self) -> None:
        from aerobim.application.services.capability_policy import build_signoff_policy
        from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

        policy = build_signoff_policy(profile="production")
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.SKIPPED, "ifcclash missing"),
            ifc_schema=CapabilityStatus(CapabilityState.OK, "ok"),
            unit_scale=CapabilityStatus(CapabilityState.OK, "ok"),
            calculation_match=CapabilityStatus(CapabilityState.OK, "ok"),
            quantity=CapabilityStatus(CapabilityState.OK, "ok"),
            mep_system_clash=CapabilityStatus(CapabilityState.OK, "ok"),
        )
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))

    def test_failed_ids_blocks_pass_even_in_development(self) -> None:
        from aerobim.application.services.capability_policy import build_signoff_policy
        from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities

        policy = build_signoff_policy(profile="development")
        caps = ReportCapabilities(
            ids=CapabilityStatus(CapabilityState.FAILED, "adapter exploded"),
        )
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))


class RuntimeLockAndFrontendHygieneTests(unittest.TestCase):
    def test_runtime_lock_excludes_pymupdf(self) -> None:
        lock = Path(__file__).resolve().parents[1] / "requirements-lock.txt"
        for line in lock.read_text(encoding="utf-8").splitlines():
            stripped = line.strip().lower().rstrip("\\").strip()
            self.assertFalse(
                stripped.startswith("pymupdf==") or stripped.startswith("pymupdf["),
                "pymupdf leaked into runtime lock",
            )

    def test_frontend_src_does_not_read_vite_bearer(self) -> None:
        src = Path(__file__).resolve().parents[2] / "frontend" / "src"
        offenders: list[str] = []
        for path in src.rglob("*"):
            if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "VITE_AEROBIM_API_BEARER_TOKEN" in text:
                offenders.append(str(path.relative_to(src)))
        self.assertEqual(offenders, [])


class PathJailFuzzTests(unittest.TestCase):
    def test_traversal_and_control_vectors_stay_jailed(self) -> None:
        from aerobim.core.security.path_jail import PathJailError, resolve_storage_path

        vectors = (
            "../outside.ifc",
            "..\\outside.ifc",
            "/etc/passwd",
            "foo/../../etc/passwd",
            "%2e%2e/outside.ifc",
            "x\x00y.ifc",
            "x\ny.ifc",
            "uploads/evil\r.ifc",
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for vector in vectors:
                with self.assertRaises(PathJailError, msg=vector):
                    resolve_storage_path(vector, base=base)

    def test_hypothesis_generated_dotdot_stays_jailed(self) -> None:
        try:
            from hypothesis import given
            from hypothesis import settings as hy_settings
            from hypothesis import strategies as st
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("hypothesis not installed") from exc

        from aerobim.core.security.path_jail import PathJailError, resolve_storage_path

        @given(st.text(min_size=1, max_size=12).map(lambda s: f"../{s or 'x'}"))
        @hy_settings(max_examples=25, deadline=None)
        def _run(raw: str) -> None:
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(PathJailError):
                    resolve_storage_path(raw, base=Path(tmp))

        _run()


class MappedLoopbackSsrfTests(unittest.TestCase):
    def test_ipv4_mapped_loopback_and_metadata_blocked(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://[::ffff:127.0.0.1]/jwks", resolve_dns=False)
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://[::ffff:169.254.169.254]/latest", resolve_dns=False)


if __name__ == "__main__":
    unittest.main()
