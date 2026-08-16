"""HD2 seam remediations (JWKS refetch, DI lock, quota stale-lock, XFF, origin hash)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aerobim.core.di.container import Container, Lifecycle
from aerobim.core.security import outbound_url
from aerobim.core.security.upload_quota import FilesystemUploadQuotaStore
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.domain.run_manifest import engine_signature
from aerobim.infrastructure.adapters.bcf_report_exporter import bcf_topic_zip_dir
from aerobim.infrastructure.security.oidc_token_validator import OidcTokenValidator, OidcValidationError
from aerobim.presentation.http.rate_limit import client_bucket_host


class _FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            return self._data
        return self._data[:size]

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


class Hd2RunManifestTests(unittest.TestCase):
    def test_engine_signature_excludes_advisory_origin_with_plain_rule_id(self) -> None:
        class _Report:
            issues = [
                ValidationIssue(
                    rule_id="SP-63-1",
                    severity=Severity.INFO,
                    category=FindingCategory.IFC_VALIDATION,
                    message="llm noise",
                    origin="advisory",
                ),
                ValidationIssue(
                    rule_id="SP-63-1",
                    severity=Severity.ERROR,
                    category=FindingCategory.IFC_VALIDATION,
                    message="engine",
                    origin="deterministic",
                ),
            ]

        sig = engine_signature(_Report())
        self.assertEqual(len(sig), 1)
        self.assertEqual(sig[0][4], "engine")


class Hd2ContainerTests(unittest.TestCase):
    def test_concurrent_singleton_factory_runs_once(self) -> None:
        container = Container()
        barrier = threading.Barrier(8)
        counter = {"value": 0}

        def factory(_container: Container) -> object:
            counter["value"] += 1
            time.sleep(0.02)
            return object()

        container.register("once", factory, lifecycle=Lifecycle.SINGLETON)

        def worker() -> None:
            barrier.wait()
            container.resolve("once")

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(counter["value"], 1)

    def test_singleton_factory_may_resolve_another_singleton(self) -> None:
        container = Container()

        def inner(_container: Container) -> str:
            return "inner"

        def outer(container_: Container) -> str:
            return f"outer-{container_.resolve('inner')}"

        container.register("inner", inner, lifecycle=Lifecycle.SINGLETON)
        container.register("outer", outer, lifecycle=Lifecycle.SINGLETON)
        self.assertEqual(container.resolve("outer"), "outer-inner")


class Hd2QuotaLockTests(unittest.TestCase):
    def test_stale_lock_is_stolen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(Path(tmp), max_uploads_per_day=10)
            path = store._path("t1", store._day())
            lock_path = path.with_suffix(path.suffix + ".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text("stale", encoding="utf-8")
            stale = time.time() - 200
            os.utime(lock_path, (stale, stale))
            snap = store.reserve("t1", size_bytes=10)
            self.assertEqual(snap.upload_count, 1)
            self.assertFalse(lock_path.exists())

    def test_stale_hold_is_released(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemUploadQuotaStore(
                Path(tmp), max_uploads_per_day=10, max_bytes_per_day=10_000
            )
            store.reserve("t1", size_bytes=100, hold_id="deadbeefcafebabe")
            self.assertEqual(store.snapshot("t1").bytes_used, 100)
            holds = list(store._root.glob("*/holds/*.json"))
            self.assertEqual(len(holds), 1)
            payload = json.loads(holds[0].read_text(encoding="utf-8"))
            payload["created_at"] = time.time() - 7200
            holds[0].write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(store.reconcile_stale_holds(max_age_seconds=3600), 1)
            self.assertEqual(store.snapshot("t1").bytes_used, 0)
            self.assertEqual(list(store._root.glob("*/holds/*.json")), [])


class Hd2UploadReserveOrderTests(unittest.TestCase):
    def test_upload_route_reserves_quota_before_writing_quarantine(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "presentation"
            / "http"
            / "routes"
            / "uploads.py"
        ).read_text(encoding="utf-8")
        reserve_at = source.index("upload_quota_store.reserve(")
        write_at = source.index('quarantine.open("wb")')
        self.assertLess(reserve_at, write_at)


class Hd2RateLimitKeyTests(unittest.TestCase):
    def test_xff_used_only_from_trusted_peer(self) -> None:
        trusted = frozenset({"10.0.0.1"})
        spoofed = SimpleNamespace(
            client=SimpleNamespace(host="8.8.8.8"),
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        proxied = SimpleNamespace(
            client=SimpleNamespace(host="10.0.0.1"),
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        self.assertEqual(client_bucket_host(spoofed, trusted), "8.8.8.8")  # type: ignore[arg-type]
        self.assertEqual(client_bucket_host(proxied, trusted), "1.2.3.4")  # type: ignore[arg-type]

    def test_non_ip_xff_falls_back_to_peer(self) -> None:
        trusted = frozenset({"10.0.0.1"})
        junk = SimpleNamespace(
            client=SimpleNamespace(host="10.0.0.1"),
            headers={"x-forwarded-for": "not-an-ip"},
        )
        self.assertEqual(client_bucket_host(junk, trusted), "10.0.0.1")  # type: ignore[arg-type]


class Hd2JwksTests(unittest.TestCase):
    def test_force_refetch_bypasses_ttl(self) -> None:
        calls = {"n": 0}

        def fake_urlopen(*_a: object, **_k: object) -> _FakeResponse:
            calls["n"] += 1
            return _FakeResponse(b'{"keys":[{"kid":"k1"}]}')

        validator = OidcTokenValidator(
            issuer="https://idp.example.com/",
            audience="aerobim",
            jwks_url="https://idp.example.com/jwks",
        )
        with (
            patch.object(outbound_url, "assert_safe_outbound_url", lambda *a, **k: ""),
            patch.object(outbound_url, "safe_urlopen", fake_urlopen),
        ):
            validator.fetch_jwks()
            validator.fetch_jwks()
            self.assertEqual(calls["n"], 1)
            validator.fetch_jwks(force=True)
            self.assertEqual(calls["n"], 2)

    def test_unknown_kid_does_not_hammer_jwks(self) -> None:
        jwt_mod = types.ModuleType("jwt")
        jwt_mod.get_unverified_header = lambda _token: {"kid": "missing"}  # type: ignore[attr-defined]

        class _PyJWK:
            @staticmethod
            def from_dict(_data: object) -> object:
                raise AssertionError("unknown kid must not build a key")

        jwt_mod.PyJWK = _PyJWK  # type: ignore[attr-defined]
        calls = {"n": 0}

        def fake_urlopen(*_a: object, **_k: object) -> _FakeResponse:
            calls["n"] += 1
            return _FakeResponse(b'{"keys":[{"kid":"k1"}]}')

        validator = OidcTokenValidator(
            issuer="https://idp.example.com/",
            audience="aerobim",
            jwks_url="https://idp.example.com/jwks",
        )
        with (
            patch.dict("sys.modules", {"jwt": jwt_mod}),
            patch.object(outbound_url, "assert_safe_outbound_url", lambda *a, **k: ""),
            patch.object(outbound_url, "safe_urlopen", fake_urlopen),
        ):
            with self.assertRaises(OidcValidationError):
                validator.validate("a.b.c")
            first = calls["n"]
            self.assertGreaterEqual(first, 1)
            with self.assertRaises(OidcValidationError):
                validator.validate("a.b.c")
            self.assertEqual(calls["n"], first)


class Hd2BcfTests(unittest.TestCase):
    def test_topic_dir_rejects_path_guid(self) -> None:
        with self.assertRaises(ValueError):
            bcf_topic_zip_dir("../escape")
        self.assertEqual(
            bcf_topic_zip_dir("550e8400-e29b-41d4-a716-446655440000"),
            "550e8400-e29b-41d4-a716-446655440000",
        )


class Hd2SettingsTests(unittest.TestCase):
    def test_production_rejects_zero_rate_limit(self) -> None:
        from aerobim.core.config.settings import Settings

        previous = {
            k: os.environ.get(k)
            for k in (
                "AEROBIM_ENV",
                "AEROBIM_SIGNOFF_PROFILE",
                "AEROBIM_API_BEARER_TOKEN",
                "AEROBIM_REDIS_URL",
                "AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE",
            )
        }
        try:
            os.environ["AEROBIM_ENV"] = "production"
            os.environ["AEROBIM_SIGNOFF_PROFILE"] = "production"
            os.environ["AEROBIM_API_BEARER_TOKEN"] = "tok"
            os.environ["AEROBIM_REDIS_URL"] = "redis://127.0.0.1:6379/0"
            os.environ["AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE"] = "0"
            with self.assertRaisesRegex(RuntimeError, "AEROBIM_HTTP_RATE_LIMIT_PER_MINUTE"):
                Settings.from_env()
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
