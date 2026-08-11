"""RT-20260811-01/06: security headers must not be overridden by extras."""

from __future__ import annotations

import unittest

from aerobim.core.security.immutable_http_headers import merge_outbound_headers
from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider
from aerobim.infrastructure.adapters.vlm_advisory_client import VlmAdvisoryClient


class ImmutableHttpHeadersMergeTests(unittest.TestCase):
    def test_forced_wins_over_extra(self) -> None:
        headers = merge_outbound_headers(
            {
                "Authorization": "Bearer ATTACK",
                "Content-Type": "text/plain",
                "Accept": "*/*",
                "Host": "evil.example",
                "X-Custom": "ok",
            },
            forced={
                "Authorization": "Bearer REAL",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self.assertEqual(headers["Authorization"], "Bearer REAL")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertEqual(headers["X-Custom"], "ok")
        self.assertNotIn("Host", headers)


class VlmImmutableSecurityHeadersTests(unittest.TestCase):
    def test_extra_headers_cannot_override_security_fields(self) -> None:
        client = VlmAdvisoryClient.__new__(VlmAdvisoryClient)
        client._auth_scheme = "Bearer"
        client._api_key = "REAL_SECRET_KEY"
        client._folder_id = "folder-real"
        client._extra_headers = {
            "Authorization": "Bearer ATTACKER",
            "Content-Type": "text/plain",
            "Accept": "*/*",
            "Host": "evil.example",
            "x-data-logging-enabled": "true",
            "x-folder-id": "folder-evil",
            "X-Trace": "keep-me",
        }
        headers = VlmAdvisoryClient._request_headers(client)
        self.assertEqual(headers["Authorization"], "Bearer REAL_SECRET_KEY")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertEqual(headers["x-data-logging-enabled"], "false")
        self.assertEqual(headers["x-folder-id"], "folder-real")
        self.assertEqual(headers["X-Trace"], "keep-me")
        self.assertNotIn("Host", headers)


class LlmImmutableSecurityHeadersTests(unittest.TestCase):
    def test_authorization_and_content_type_forced(self) -> None:
        provider = OpenAICompatLlmProvider.__new__(OpenAICompatLlmProvider)
        provider._auth_scheme = "Bearer"
        provider._api_key = "REAL"
        provider._folder_id = "folder-from-ctor"
        provider._extra_headers = {
            "Authorization": "Bearer ATTACK",
            "Content-Type": "evil",
            "Accept": "*/*",
            "Host": "evil.example",
            "x-folder-id": "folder-from-extra",
            "x-data-logging-enabled": "false",
            "X-Custom": "ok",
        }
        headers = OpenAICompatLlmProvider._request_headers(
            provider, client_request_id="11111111-1111-4111-8111-111111111111"
        )
        self.assertEqual(headers["Authorization"], "Bearer REAL")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertEqual(headers["x-folder-id"], "folder-from-ctor")
        self.assertEqual(headers["x-data-logging-enabled"], "false")
        self.assertEqual(headers["X-Custom"], "ok")
        self.assertEqual(
            headers["x-client-request-id"],
            "11111111-1111-4111-8111-111111111111",
        )


if __name__ == "__main__":
    unittest.main()
