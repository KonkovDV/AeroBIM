from __future__ import annotations

import socket
import sys
import unittest
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

    def test_build_frontend_env_points_at_backend_base_url(self) -> None:
        env = build_frontend_env(
            base_env={"PATH": "example"}, backend_base_url="http://127.0.0.1:8081"
        )

        self.assertEqual(env["PATH"], "example")
        self.assertEqual(env["VITE_AEROBIM_API_BASE_URL"], "http://127.0.0.1:8081")

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
            'browser warning line\n'
            'another log line\n'
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
