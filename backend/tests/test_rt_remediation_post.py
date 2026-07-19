"""Red Team remediation regression: POST-01…11 negative tests."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from aerobim.application.services.capability_policy import build_signoff_policy
from aerobim.core.config.settings import Settings
from aerobim.core.security.outbound_url import UnsafeOutboundUrlError, assert_safe_outbound_url
from aerobim.core.security.zip_limits import ZipBombError, inspect_zip_bytes
from aerobim.domain.models import (
    CapabilityState,
    CapabilityStatus,
    ReportCapabilities,
)
from aerobim.presentation.http.api import _esc


class Post01ProductionSignoffDefaultTests(unittest.TestCase):
    def test_production_env_defaults_to_production_signoff(self) -> None:
        previous = {
            k: os.environ.get(k)
            for k in ("AEROBIM_ENV", "AEROBIM_SIGNOFF_PROFILE", "AEROBIM_API_BEARER_TOKEN")
        }
        try:
            os.environ["AEROBIM_ENV"] = "production"
            os.environ.pop("AEROBIM_SIGNOFF_PROFILE", None)
            os.environ["AEROBIM_API_BEARER_TOKEN"] = "tok"
            settings = Settings.from_env()
            self.assertEqual(settings.signoff_profile, "production")
            self.assertTrue(settings.require_clash)
            self.assertTrue(settings.require_bsi_schema)
            self.assertTrue(settings.require_mep_system_clash)
            self.assertTrue(settings.clash_affects_pass)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class Post03SsrfGuardTests(unittest.TestCase):
    def test_rejects_metadata_and_loopback(self) -> None:
        for url in (
            "http://169.254.169.254/latest/meta-data/",
            "http://127.0.0.1/admin",
            "http://[::1]/",
            "https://localhost/jwks",
        ):
            with self.assertRaises(UnsafeOutboundUrlError):
                assert_safe_outbound_url(url, allow_http=True, resolve_dns=False)

    def test_rejects_userinfo_and_http_by_default(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://user:pass@example.com/x", resolve_dns=False)
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("http://example.com/x", resolve_dns=False)


class Post06UnitScaleAndPilotSkippedTests(unittest.TestCase):
    def test_pilot_blocks_unverified_unit_scale_and_skipped_quantity(self) -> None:
        policy = build_signoff_policy(profile="samolet_pilot")
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.OK),
            ifc_schema=CapabilityStatus(CapabilityState.OK),
            mep_system_clash=CapabilityStatus(CapabilityState.OK),
            unit_scale=CapabilityStatus(CapabilityState.NOT_VERIFIED, "not probed"),
            calculation_match=CapabilityStatus(CapabilityState.SKIPPED, "n/a"),
            quantity=CapabilityStatus(CapabilityState.SKIPPED, "n/a"),
        )
        blocked = policy.required_capability_blocks_pass(caps)
        self.assertIn("unit_scale", blocked)
        self.assertIn("calculation_match", blocked)
        self.assertIn("quantity", blocked)
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))


class Post10HtmlEscapeTests(unittest.TestCase):
    def test_escapes_single_quotes_for_attributes(self) -> None:
        self.assertIn("&#x27;", _esc("O'Brien"))
        self.assertNotIn("'", _esc("sev' onclick='alert(1)"))


class Post11ZipTraversalTests(unittest.TestCase):
    def test_rejects_dotdot_members(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("../evil.txt", b"x")
        with self.assertRaises(ZipBombError):
            inspect_zip_bytes(buf.getvalue())


class Post08UploadOmitsObjectKeyTests(unittest.TestCase):
    def test_upload_response_has_no_object_key(self) -> None:
        try:
            from fastapi.testclient import TestClient
        except ModuleNotFoundError as exc:
            raise unittest.SkipTest("FastAPI/httpx not installed") from exc

        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.presentation.http.api import create_http_app

        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(
                application_name="aerobim-test",
                environment="test",
                host="127.0.0.1",
                port=8080,
                storage_dir=Path(tmp),
                debug=True,
                allow_anonymous_dev=True,
            )
            client = TestClient(create_http_app(bootstrap_container(settings)))
            response = client.post(
                "/v1/uploads",
                files={"file": ("pilot.ifc", b"ISO-10303-21;", "application/octet-stream")},
            )
            self.assertEqual(response.status_code, 200, response.text)
            body = response.json()
            self.assertNotIn("object_key", body)


if __name__ == "__main__":
    unittest.main()
