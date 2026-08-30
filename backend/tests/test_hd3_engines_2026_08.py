"""HD3 engine/store remediations: IDS silence, clash mapper, IFC LRU, BFF authz."""

from __future__ import annotations

import inspect
import unittest

from aerobim.domain.errors import ClashCapabilityError
from aerobim.infrastructure.adapters.ifc_clash_detector import clash_results_from_sets
from aerobim.infrastructure.auth.oidc_bff_phase3 import (
    OidcBffSession,
    parse_session_cookie,
    require_verified_bff_session,
    sign_session_cookie,
)


class Hd3ClashMapperTests(unittest.TestCase):
    def test_malformed_clash_records_fail_closed(self) -> None:
        with self.assertRaises(ClashCapabilityError) as ctx:
            clash_results_from_sets([{"clashes": ["not-a-mapping"]}])
        self.assertEqual(ctx.exception.status, "failed")

    def test_empty_clash_mapping_is_clean(self) -> None:
        self.assertEqual(clash_results_from_sets([{"clashes": {}}]), [])

    def test_clash_without_guids_fail_closed(self) -> None:
        with self.assertRaises(ClashCapabilityError) as ctx:
            clash_results_from_sets([{"clashes": {"1": {"a_name": "Pipe", "b_name": "Duct"}}}])
        self.assertEqual(ctx.exception.status, "failed")


class Hd3BffTests(unittest.TestCase):
    def test_non_ascii_session_cookie_is_rejected(self) -> None:
        self.assertIsNone(parse_session_cookie("сессия.deadbeef", "secret"))

    def test_lab_session_cannot_authorize(self) -> None:
        lab = OidcBffSession(
            session_id="abc",
            subject="user",
            created_at=0.0,
            identity_verified=False,
        )
        with self.assertRaises(PermissionError):
            require_verified_bff_session(lab)

    def test_verified_session_passes_authz_gate(self) -> None:
        session = OidcBffSession(
            session_id="abc",
            subject="user",
            created_at=0.0,
            identity_verified=True,
        )
        self.assertIs(require_verified_bff_session(session), session)

    def test_signed_cookie_roundtrip_ascii(self) -> None:
        token = sign_session_cookie("sid123", "secret")
        self.assertEqual(parse_session_cookie(token, "secret"), "sid123")

    def test_api_bearer_auth_does_not_accept_session_cookie(self) -> None:
        from aerobim.presentation.http.context import ApiContext

        params = inspect.signature(ApiContext.require_bearer_auth).parameters
        self.assertIn("authorization", params)
        self.assertFalse(any("cookie" in name.lower() for name in params))
        source = inspect.getsource(ApiContext.require_bearer_auth)
        self.assertIn("BFF lab cookies are never accepted", source)
        self.assertIn("HD3-BFF-01", source)


class Hd3IfcLruTests(unittest.TestCase):
    def test_cache_evicts_beyond_max_models(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import (
            _memory,
            configure_ifc_parse_cache,
            ifc_parse_cache_stats,
            reset_ifc_parse_cache_for_tests,
        )

        reset_ifc_parse_cache_for_tests()
        configure_ifc_parse_cache(None, max_models=2)
        from aerobim.infrastructure.adapters import ifc_file_open as mod

        with mod._lock:
            mod._memory[("a", 1, 1)] = object()
            mod._memory[("b", 1, 1)] = object()
            mod._memory[("c", 1, 1)] = object()
            mod._evict_overflow_locked()
        self.assertEqual(len(_memory), 2)
        self.assertGreaterEqual(ifc_parse_cache_stats()["evictions"], 1)
        reset_ifc_parse_cache_for_tests()

    def test_ram_ceiling_is_eight_times_256_mib(self) -> None:
        from aerobim.infrastructure.adapters.ifc_file_open import (
            ifc_cache_ram_ceiling_bytes,
            ifc_cache_ram_ceiling_payload,
        )

        self.assertEqual(ifc_cache_ram_ceiling_bytes(), 8 * 256 * 1024 * 1024)
        payload = ifc_cache_ram_ceiling_payload()
        self.assertEqual(payload["ceiling_bytes"], 2147483648)
        self.assertIsNone(payload["measured_rss_delta_bytes"])
        self.assertTrue(payload["literature_rss_not_measured"])
        self.assertEqual(payload["spf_ram_multiplier_literature"], 10)
        self.assertEqual(payload["literature_rss_ceiling_bytes"], 10 * 8 * 256 * 1024 * 1024)
        self.assertFalse(payload["closes_rt003"])
        self.assertFalse(payload["representative_scale"])
        self.assertEqual(payload["checkpoint"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
