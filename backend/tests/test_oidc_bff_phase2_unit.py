"""Phase 2.5 unit coverage for OIDC BFF PKCE stubs."""

from __future__ import annotations

import unittest

from aerobim.domain.system_capabilities import build_auth_bff_capability
from aerobim.infrastructure.auth.oidc_bff_stubs import (
    InMemoryOidcBffStateStore,
    build_callback_stub_payload,
    build_login_stub_payload,
    build_logout_stub_payload,
)


class OidcBffPhase2UnitTests(unittest.TestCase):
    def test_capability_stays_not_implemented(self) -> None:
        payload = build_auth_bff_capability()
        self.assertEqual(payload["status"], "NOT_IMPLEMENTED")
        self.assertIn("phase_2_stubs", payload)
        self.assertIn("phase_2_5_pkce", payload)

    def test_state_one_time_and_payload_honesty(self) -> None:
        store = InMemoryOidcBffStateStore()
        entry = store.issue()
        self.assertIsNotNone(store.consume(entry.state))
        self.assertIsNone(store.consume(entry.state))
        login = build_login_stub_payload(state_entry=entry)
        self.assertIsNone(login.get("idp_redirect_url"))
        self.assertIn("pkce", login)
        callback = build_callback_stub_payload(state=entry.state, code="x")
        self.assertFalse(callback["session_cookie_issued"])
        self.assertEqual(build_logout_stub_payload()["status"], "NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
