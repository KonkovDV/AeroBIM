"""RTATOM Wave A2.5 / A3 hygiene regressions (2026-07-20)."""

from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.core.security.outbound_url import (
    UnsafeOutboundUrlError,
    assert_oidc_jwks_host_bound,
)
from aerobim.core.security.path_jail import (
    PathJailError,
    open_storage_file,
    safe_storage_token,
)
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_path
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.presentation.http.api import create_http_app


class InspectZipPathStreamTests(unittest.TestCase):
    def test_inspect_zip_path_does_not_call_read_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "sample.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("ok.txt", b"hello")

            original_read_bytes = Path.read_bytes

            def _fail_read_bytes(self: Path) -> bytes:  # noqa: ANN001
                if self == archive_path or self.resolve() == archive_path.resolve():
                    raise AssertionError("inspect_zip_path must not call Path.read_bytes()")
                return original_read_bytes(self)

            with patch.object(Path, "read_bytes", _fail_read_bytes):
                result = inspect_zip_path(archive_path)
            self.assertEqual(result.member_count, 1)

    def test_inspect_zip_path_rejects_oversized_archive_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "huge.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("ok.txt", b"hello")
            with self.assertRaises(ZipBombError):
                inspect_zip_path(archive_path, max_archive_file_bytes=1)


class NfkcStorageTokenTests(unittest.TestCase):
    def test_compatibility_chars_normalize_before_encode(self) -> None:
        # U+FF21 is fullwidth Latin 'A' → NFKC → 'A'
        fullwidth = safe_storage_token("\uff21enant")
        plain = safe_storage_token("Aenant")
        self.assertEqual(fullwidth, plain)
        self.assertEqual(plain, "Aenant")


class SecurityHeadersTests(unittest.TestCase):
    def test_health_sets_asvs_headers(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError:
            self.skipTest("fastapi not installed")

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=False,
                allow_anonymous_dev=True,
            )
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
            self.assertEqual(response.headers.get("referrer-policy"), "no-referrer")
            self.assertEqual(response.headers.get("x-frame-options"), "DENY")
            csp = response.headers.get("content-security-policy") or ""
            self.assertIn("default-src 'none'", csp)
            self.assertIn("frame-ancestors 'none'", csp)


class OidcJwksHostBindTests(unittest.TestCase):
    def test_mismatch_raises(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_oidc_jwks_host_bound(
                "https://issuer.example.com/",
                "https://evil.example.net/jwks.json",
            )

    def test_extra_host_allow_works(self) -> None:
        assert_oidc_jwks_host_bound(
            "https://login.microsoftonline.com/tenant/v2.0",
            "https://login.microsoft.com/common/discovery/keys",
            extra_hosts=("login.microsoft.com",),
        )

    def test_settings_from_env_rejects_mismatched_jwks(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_OIDC_ISSUER": "https://issuer.example.com/",
            "AEROBIM_OIDC_AUDIENCE": "api://aerobim",
            "AEROBIM_OIDC_JWKS_URL": "https://evil.example.net/jwks.json",
            "AEROBIM_ALLOW_ANONYMOUS_DEV": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaises(RuntimeError):
                Settings.from_env()


class OpenStorageFileTests(unittest.TestCase):
    def test_open_storage_file_reads_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            target = base / "report.json"
            target.write_text('{"ok": true}', encoding="utf-8")
            with open_storage_file(target, base=base, mode="rb") as handle:
                self.assertEqual(handle.read(), b'{"ok": true}')

    def test_open_storage_file_rejects_symlink_when_creatable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            target = base / "real.json"
            target.write_text('{"ok": true}', encoding="utf-8")
            link = base / "link.json"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not creatable on this platform/user")
            with self.assertRaises(PathJailError):
                open_storage_file(link, base=base, mode="rb")


class XmlLimitsTests(unittest.TestCase):
    def test_safe_fromstring_rejects_oversized_payload(self) -> None:
        from aerobim.core.security.xml_limits import XmlBombError, safe_fromstring

        with self.assertRaises(XmlBombError):
            safe_fromstring(b"<root/>" + b"x" * 64, max_bytes=8)

    def test_safe_fromstring_rejects_too_many_elements(self) -> None:
        from aerobim.core.security.xml_limits import XmlBombError, safe_fromstring

        payload = b"<root>" + b"<e/>" * 20 + b"</root>"
        with self.assertRaises(XmlBombError):
            safe_fromstring(payload, max_elements=5)

    def test_safe_parse_roundtrip(self) -> None:
        from aerobim.core.security.xml_limits import safe_parse

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.xml"
            path.write_text("<ids><info/></ids>", encoding="utf-8")
            tree = safe_parse(path)
            self.assertEqual(tree.getroot().tag, "ids")


class AuthBffHonestyTests(unittest.TestCase):
    def test_capabilities_auth_bff_not_implemented(self) -> None:
        from aerobim.domain.system_capabilities import build_system_capabilities_payload

        payload = build_system_capabilities_payload()
        self.assertEqual(payload["schema_version"], "1.2.0")
        auth_bff = payload["auth_bff"]
        assert isinstance(auth_bff, dict)
        self.assertEqual(auth_bff["status"], "NOT_IMPLEMENTED")
        design = str(auth_bff["design"])
        self.assertTrue(Path(design).as_posix().endswith("POST05_OIDC_BFF_DESIGN_2026_07.md"))


if __name__ == "__main__":
    unittest.main()
