"""Red Team Wave 4 remediation — August 2026."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from aerobim.core.security.rate_limit_backend import InProcessRateLimitBackend
from aerobim.domain.auth_roles import extract_oidc_roles, principal_has_any_role
from aerobim.domain.object_acl import AuthPrincipal, principal_may_append_hitl_event
from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend
from aerobim.infrastructure.security.redis_rate_limiter import RedisRateLimitBackend


class OidcRoleExtractionTests(unittest.TestCase):
    def test_flat_roles_claim(self) -> None:
        roles = extract_oidc_roles({"roles": ["Reviewer", "viewer"]}, roles_claim="roles")
        self.assertIn("reviewer", roles)
        self.assertIn("viewer", roles)

    def test_nested_realm_access_roles(self) -> None:
        roles = extract_oidc_roles(
            {"realm_access": {"roles": ["hitl_reviewer"]}},
            roles_claim="realm_access.roles",
        )
        self.assertIn("hitl_reviewer", roles)


class HitlRbacRoleGateTests(unittest.TestCase):
    def test_oidc_without_reviewer_role_denied_in_production(self) -> None:
        principal = AuthPrincipal(
            tenant_id="t1",
            subject="user-1",
            roles=frozenset({"viewer"}),
        )
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=True,
                require_hitl_reviewer_roles=True,
                principal=principal,
                event_type="accepted",
            )
        )

    def test_oidc_with_expert_alias_allowed(self) -> None:
        principal = AuthPrincipal(
            tenant_id="t1",
            subject="user-1",
            roles=frozenset({"expert"}),
        )
        self.assertTrue(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=True,
                require_hitl_reviewer_roles=True,
                principal=principal,
                event_type="accepted",
            )
        )

    def test_oidc_user_alias_denied_in_production(self) -> None:
        principal = AuthPrincipal(
            tenant_id="t1",
            subject="user-1",
            roles=frozenset({"user"}),
        )
        self.assertFalse(
            principal_may_append_hitl_event(
                enforce_hitl_reviewer_auth=True,
                require_hitl_reviewer_roles=True,
                principal=principal,
                event_type="accepted",
            )
        )


class RateLimitBackendTests(unittest.TestCase):
    def test_in_process_limiter_blocks_over_quota(self) -> None:
        backend = InProcessRateLimitBackend()
        for _ in range(3):
            self.assertTrue(
                backend.allow(bucket="post", key="k", max_events=3, window_seconds=60.0)
            )
        self.assertFalse(backend.allow(bucket="post", key="k", max_events=3, window_seconds=60.0))

    def test_redis_backend_uses_script(self) -> None:
        backend = RedisRateLimitBackend.__new__(RedisRateLimitBackend)
        backend._prefix = "pfx:"
        script = MagicMock(return_value=1)
        backend._script = script
        self.assertTrue(
            backend.allow(bucket="post", key="client", max_events=5, window_seconds=60.0)
        )
        script.assert_called_once()

    def test_build_backend_falls_back_without_redis_url(self) -> None:
        backend = build_rate_limit_backend(None)
        self.assertIsInstance(backend, InProcessRateLimitBackend)

    def test_in_process_backend_caps_key_count(self) -> None:
        backend = InProcessRateLimitBackend(max_keys=2)
        self.assertTrue(backend.allow(bucket="post", key="a", max_events=10, window_seconds=60.0))
        self.assertTrue(backend.allow(bucket="post", key="b", max_events=10, window_seconds=60.0))
        self.assertTrue(backend.allow(bucket="post", key="c", max_events=10, window_seconds=60.0))
        self.assertLessEqual(len(backend._events), 2)


class RoleHelperTests(unittest.TestCase):
    def test_principal_has_any_role_case_insensitive(self) -> None:
        self.assertTrue(
            principal_has_any_role(
                principal_roles=frozenset({"admin"}),
                required=frozenset({"Admin"}),
            )
        )


if __name__ == "__main__":
    unittest.main()
