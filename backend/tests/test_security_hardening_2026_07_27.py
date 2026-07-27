"""Security hardening wave (2026-07-27) — regression tests for the private
advisory findings F-01..F-03.

F-01  HTML export must escape a non-enum ``category`` label (defense-in-depth).
F-02  LocalObjectStore.presign_get must not hand out a reference to an object
      exceeding the streaming get cap.
F-03  OIDC JWKS fetch must reject an oversized response body (memory DoS).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.security import outbound_url
from aerobim.core.security.object_limits import ObjectTooLargeError
from aerobim.infrastructure.adapters.local_object_store import LocalObjectStore
from aerobim.infrastructure.security.oidc_token_validator import (
    OidcTokenValidator,
    OidcValidationError,
)
from aerobim.presentation.http.report_html import render_report_html


class HtmlExportLabelEscapeTests(unittest.TestCase):
    """F-01: a tampered stored report with a non-enum category cannot inject HTML."""

    def _minimal_data(self, category: str) -> dict:
        return {
            "summary": {
                "passed": True,
                "issue_count": 1,
                "error_count": 0,
                "warning_count": 0,
                "requirement_count": 0,
            },
            "issues": [
                {
                    "category": category,
                    "rule_id": "R1",
                    "message": "m",
                    "severity": "info",
                }
            ],
        }

    def test_non_enum_category_label_is_escaped(self) -> None:
        payload = "<img src=x onerror=alert(1)>"
        html = render_report_html("a" * 32, self._minimal_data(payload))
        self.assertNotIn(payload, html)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", html)

    def test_known_category_label_stays_static(self) -> None:
        html = render_report_html("b" * 32, self._minimal_data("spatial"))
        self.assertIn("Spatial / Clash Coordination", html)


class LocalPresignCapTests(unittest.TestCase):
    """F-02: local presign must enforce parity with the get_bytes size cap."""

    def test_presign_rejects_oversized_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir), max_get_bytes=8)
            key = store.put_bytes("big.bin", b"0123456789")
            with self.assertRaises(ObjectTooLargeError):
                store.presign_get(key)

    def test_presign_allows_within_cap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LocalObjectStore(Path(tmpdir), max_get_bytes=1024)
            key = store.put_bytes("ok.bin", b"small")
            self.assertIsNotNone(store.presign_get(key))


class _FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._data
        return self._data[:size]


class JwksResponseCapTests(unittest.TestCase):
    """F-03: an oversized JWKS body must fail closed, never buffer unbounded.

    ``fetch_jwks`` re-imports the guard names from ``outbound_url`` on each call,
    so patching that module reaches the local import. Patches auto-restore via
    ``patch.object`` so the SSRF guard is never left globally disabled.
    """

    def _validator(self) -> OidcTokenValidator:
        return OidcTokenValidator(
            issuer="https://idp.example.com/",
            audience="aerobim",
            jwks_url="https://idp.example.com/jwks",
        )

    def test_oversized_jwks_rejected(self) -> None:
        oversized = b'{"keys":[]}' + b" " * (2 * 1024 * 1024)
        with (
            patch.object(outbound_url, "assert_safe_outbound_url", lambda *a, **k: ""),
            patch.object(outbound_url, "safe_urlopen", lambda *a, **k: _FakeResponse(oversized)),
        ):
            with self.assertRaises(OidcValidationError):
                self._validator().fetch_jwks()

    def test_small_jwks_accepted(self) -> None:
        small = b'{"keys":[{"kid":"k1"}]}'
        with (
            patch.object(outbound_url, "assert_safe_outbound_url", lambda *a, **k: ""),
            patch.object(outbound_url, "safe_urlopen", lambda *a, **k: _FakeResponse(small)),
        ):
            payload = self._validator().fetch_jwks()
        self.assertEqual(payload, {"keys": [{"kid": "k1"}]})


if __name__ == "__main__":
    unittest.main()
