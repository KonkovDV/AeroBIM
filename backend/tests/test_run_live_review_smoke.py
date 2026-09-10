from __future__ import annotations

import io
import socket
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.tools.run_live_review_smoke import (
    build_backend_env,
    build_frontend_env,
    choose_available_port,
    extract_json_payload,
    open_http_url,
)
from aerobim.tools.seed_smoke_report import SMOKE_TENANT_ID


class LiveReviewSmokeHelperTests(unittest.TestCase):
    def test_choose_available_port_prefers_requested_free_port(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            candidate = probe.getsockname()[1]

        selected = choose_available_port("127.0.0.1", (candidate,))

        self.assertEqual(selected, candidate)

    def test_choose_available_port_falls_back_when_preferred_port_is_busy(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reserved:
            reserved.bind(("127.0.0.1", 0))
            reserved.listen(1)
            busy_port = reserved.getsockname()[1]

            selected = choose_available_port("127.0.0.1", (busy_port,))

        self.assertNotEqual(selected, busy_port)

    def test_build_backend_env_sets_storage_port_debug_and_cors(self) -> None:
        env = build_backend_env(
            base_env={"PATH": "example"},
            storage_dir=Path("c:/tmp/live-smoke"),
            port=8081,
            frontend_origin="http://127.0.0.1:3000",
        )

        self.assertEqual(env["PATH"], "example")
        self.assertEqual(env["AEROBIM_STORAGE_DIR"], str(Path("c:/tmp/live-smoke")))
        self.assertEqual(env["AEROBIM_PORT"], "8081")
        self.assertEqual(env["AEROBIM_DEBUG"], "true")
        self.assertEqual(env["AEROBIM_CORS_ORIGINS"], "http://127.0.0.1:3000")
        self.assertEqual(env["AEROBIM_HOST"], "127.0.0.1")
        self.assertEqual(env["AEROBIM_SIGNOFF_PROFILE"], "development")

    def test_build_backend_env_binds_the_dev_principal_to_the_seeded_tenant(self) -> None:
        env = build_backend_env(
            base_env={"AEROBIM_API_BEARER_TOKEN": "inherited-token"},
            storage_dir=Path("c:/tmp/live-smoke"),
            port=8081,
            frontend_origin="http://127.0.0.1:3000",
        )

        self.assertEqual(env["AEROBIM_ENV"], "development")
        self.assertEqual(env["AEROBIM_ALLOW_ANONYMOUS_DEV"], "true")
        self.assertEqual(env["AEROBIM_API_TENANT_ID"], SMOKE_TENANT_ID)
        self.assertEqual(env["AEROBIM_PRIORITY_PROFILE"], "samolet")
        self.assertEqual(env["AEROBIM_REMARK_LOCALE"], "ru")
        # An inherited token disables the anonymous branch; the browser calls the
        # backend directly and has no way to present one.
        self.assertNotIn("AEROBIM_API_BEARER_TOKEN", env)

    def test_build_backend_env_drops_inherited_pilot_signoff(self) -> None:
        env = build_backend_env(
            base_env={"AEROBIM_SIGNOFF_PROFILE": "samolet_pilot"},
            storage_dir=Path("c:/tmp/live-smoke"),
            port=8081,
            frontend_origin="http://127.0.0.1:3000",
        )
        self.assertEqual(env["AEROBIM_SIGNOFF_PROFILE"], "development")
        self.assertEqual(env["AEROBIM_ENV"], "development")

    def test_build_frontend_env_points_at_backend_base_url(self) -> None:
        env = build_frontend_env(
            base_env={
                "PATH": "example",
                "PLAYWRIGHT_BROWSERS_PATH": "C:\\tmp\\cursor-sandbox-cache\\playwright",
            },
            backend_base_url="http://127.0.0.1:8081",
        )

        self.assertEqual(env["PATH"], "example")
        self.assertEqual(env["VITE_AEROBIM_API_BASE_URL"], "http://127.0.0.1:8081")
        self.assertEqual(env["AEROBIM_PROXY_TARGET"], "http://127.0.0.1:8081")
        self.assertNotIn("PLAYWRIGHT_BROWSERS_PATH", env)

    def test_python_deflated_zip_writes_sizes_in_the_local_header(self) -> None:
        """OA-21 BCF scan in Node rejects data-descriptor zips; Python BCF uses this shape."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("guid/markup.bcf", "<Description>Репетиция стенда</Description>")
        data = buffer.getvalue()
        self.assertEqual(int.from_bytes(data[0:4], "little"), 0x04034B50)
        flags = int.from_bytes(data[6:8], "little")
        self.assertEqual(flags & 0x8, 0)
        compressed_size = int.from_bytes(data[18:22], "little")
        self.assertGreater(compressed_size, 0)

    def test_extract_decision_payload_ignores_step_logs(self) -> None:
        from aerobim.tools.run_live_review_smoke import extract_decision_payload

        mixed = (
            '[decision-smoke] findings-list {"issueCards":1}\n'
            '{\n  "ok": true,\n  "externalOrigins": []\n}\n'
            "browser warning line\n"
        )
        payload = extract_decision_payload(mixed)
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["externalOrigins"], [])

    def test_extract_decision_payload_ignores_demo_seed_payload(self) -> None:
        from aerobim.tools.run_live_review_smoke import extract_decision_payload

        mixed = (
            '{"ok": true, "demoSeed": true, "externalOrigins": []}\n'
            '{"ok": true, "externalOrigins": ["blob:"], "oa21": {"draft": {}}}\n'
        )
        payload = extract_decision_payload(mixed)
        self.assertIn("oa21", payload)
        self.assertNotEqual(payload.get("demoSeed"), True)

    def test_extract_demo_payload_requires_demo_seed_flag(self) -> None:
        from aerobim.tools.run_live_review_smoke import extract_demo_payload

        mixed = (
            '{"ok": true, "externalOrigins": []}\n'
            '{"ok": true, "demoSeed": true, "overlayPresent": false, "issueCount": 2}\n'
        )
        payload = extract_demo_payload(mixed)
        self.assertTrue(payload["demoSeed"])
        self.assertEqual(payload["issueCount"], 2)

    def test_extract_json_payload_ignores_prefix_lines(self) -> None:
        prefixed_payload = (
            'prefix line\n> script banner\n{\n  "trace": "artifact.zip",\n'
            '  "screenshots": {"issue": "a.png"}\n}\n'
        )
        payload = extract_json_payload(prefixed_payload)

        self.assertEqual(payload["trace"], "artifact.zip")
        self.assertEqual(payload["screenshots"]["issue"], "a.png")

    def test_extract_json_payload_ignores_suffix_lines(self) -> None:
        mixed_payload = (
            '{\n  "trace": "artifact.zip",\n  "screenshots": {"issue": "a.png"}\n}\n'
            "browser warning line\n"
            "another log line\n"
        )

        payload = extract_json_payload(mixed_payload)

        self.assertEqual(payload["trace"], "artifact.zip")
        self.assertEqual(payload["screenshots"]["issue"], "a.png")

    @patch("aerobim.tools.run_live_review_smoke.urlopen")
    @patch("aerobim.tools.run_live_review_smoke.build_opener")
    def test_open_http_url_bypasses_proxy_for_loopback_hosts(
        self, build_opener_mock: Mock, urlopen_mock: Mock
    ) -> None:
        opener = Mock()
        build_opener_mock.return_value = opener

        open_http_url("http://127.0.0.1:8080/health", timeout=7)

        build_opener_mock.assert_called_once()
        opener.open.assert_called_once_with("http://127.0.0.1:8080/health", timeout=7)
        urlopen_mock.assert_not_called()

    @patch("aerobim.tools.run_live_review_smoke.urlopen")
    @patch("aerobim.tools.run_live_review_smoke.build_opener")
    def test_open_http_url_uses_default_urlopen_for_non_loopback_hosts(
        self, build_opener_mock: Mock, urlopen_mock: Mock
    ) -> None:
        open_http_url("http://example.test:8080/health", timeout=9)

        urlopen_mock.assert_called_once_with("http://example.test:8080/health", timeout=9)
        build_opener_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
