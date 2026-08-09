"""SSRF: block 6to4 / NAT64 / Teredo translation prefixes (C-2 cheap close)."""

from __future__ import annotations

import unittest

from aerobim.core.security.outbound_url import (
    UnsafeOutboundUrlError,
    _is_blocked_ip,
    assert_safe_outbound_url,
)


class OutboundTranslationPrefixTests(unittest.TestCase):
    def test_translation_prefixes_are_blocked(self) -> None:
        self.assertTrue(_is_blocked_ip("2002:7f00:1::1"))
        self.assertTrue(_is_blocked_ip("64:ff9b::7f00:1"))
        self.assertTrue(_is_blocked_ip("64:ff9b:1::1"))
        self.assertTrue(_is_blocked_ip("2001:0:4136:e378:8000:63bf:3fff:fdd2"))

    def test_url_with_6to4_literal_rejected(self) -> None:
        with self.assertRaises(UnsafeOutboundUrlError):
            assert_safe_outbound_url("https://[2002:7f00:1::1]/jwks", resolve_dns=False)


class PublicErrorDetailHonestyTests(unittest.TestCase):
    def test_storage_boundary_detail_has_no_path_chars(self) -> None:
        from aerobim.presentation.http.errors import public_storage_boundary_detail

        detail = public_storage_boundary_detail()
        self.assertNotIn("\\", detail)
        self.assertNotIn("/", detail)
        self.assertNotIn("C:", detail)


if __name__ == "__main__":
    unittest.main()
