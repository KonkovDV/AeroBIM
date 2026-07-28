"""Hybrid AI P0: data classification + fail-closed routing policy (brief §5/§6/§21).

Verifies the class × target matrix, fail-closed defaults (unknown tenant, SECRET,
public egress for CONFIDENTIAL/RESTRICTED), the never-downgrade rule, and that no
BLOCKED/HUMAN_REVIEW decision permits an external call. Domain-pure; no verdict.
"""

from __future__ import annotations

import unittest

from aerobim.domain.hybrid import (
    DataClassification,
    RouteStatus,
    RouteTarget,
    classify_object,
    decide_route,
    most_restrictive,
    rank,
)

_C = DataClassification
_T = RouteTarget


class DataClassificationTests(unittest.TestCase):
    def test_known_kinds_map_to_expected_levels(self) -> None:
        self.assertEqual(classify_object("ifc"), _C.CONFIDENTIAL)
        self.assertEqual(classify_object("drawing"), _C.CONFIDENTIAL)
        self.assertEqual(classify_object("customer_corpus"), _C.RESTRICTED)
        self.assertEqual(classify_object("samolet_data"), _C.RESTRICTED)
        self.assertEqual(classify_object("api_key"), _C.SECRET)
        self.assertEqual(classify_object("public_fixture"), _C.PUBLIC)
        self.assertEqual(classify_object("internal_doc"), _C.INTERNAL)

    def test_unknown_kind_is_conservative_not_public(self) -> None:
        self.assertEqual(classify_object("totally-unknown-kind"), _C.CONFIDENTIAL)
        self.assertEqual(classify_object(""), _C.CONFIDENTIAL)

    def test_rank_is_strictly_increasing(self) -> None:
        ranks = [
            rank(c) for c in (_C.PUBLIC, _C.INTERNAL, _C.CONFIDENTIAL, _C.RESTRICTED, _C.SECRET)
        ]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(len(set(ranks)), 5)

    def test_most_restrictive_never_downgrades(self) -> None:
        self.assertEqual(most_restrictive(_C.PUBLIC, _C.RESTRICTED), _C.RESTRICTED)
        self.assertEqual(most_restrictive(_C.CONFIDENTIAL, _C.INTERNAL), _C.CONFIDENTIAL)
        self.assertEqual(most_restrictive(_C.SECRET, _C.PUBLIC), _C.SECRET)
        # Empty aggregate stays conservative (not PUBLIC).
        self.assertEqual(most_restrictive(), _C.CONFIDENTIAL)


class RoutingPolicyTests(unittest.TestCase):
    def test_public_class_all_targets(self) -> None:
        self.assertEqual(
            decide_route(classification=_C.PUBLIC, target=_T.LOCAL, tenant_id="t").status,
            RouteStatus.LOCAL,
        )
        self.assertEqual(
            decide_route(classification=_C.PUBLIC, target=_T.PRIVATE, tenant_id="t").status,
            RouteStatus.PRIVATE,
        )
        self.assertEqual(
            decide_route(classification=_C.PUBLIC, target=_T.PUBLIC, tenant_id="t").status,
            RouteStatus.PUBLIC_MASKED,
        )

    def test_confidential_public_is_blocked_no_egress(self) -> None:
        d = decide_route(classification=_C.CONFIDENTIAL, target=_T.PUBLIC, tenant_id="t")
        self.assertEqual(d.status, RouteStatus.BLOCKED)
        self.assertFalse(d.allowed)
        self.assertFalse(d.external_call)

    def test_restricted_public_is_blocked(self) -> None:
        d = decide_route(classification=_C.RESTRICTED, target=_T.PUBLIC, tenant_id="t")
        self.assertEqual(d.status, RouteStatus.BLOCKED)
        self.assertFalse(d.external_call)

    def test_confidential_private_requires_confirmed_mode(self) -> None:
        blocked = decide_route(classification=_C.CONFIDENTIAL, target=_T.PRIVATE, tenant_id="t")
        self.assertEqual(blocked.status, RouteStatus.BLOCKED)
        self.assertEqual(blocked.required_permission, "private_mode_confirmed")
        ok = decide_route(
            classification=_C.CONFIDENTIAL,
            target=_T.PRIVATE,
            tenant_id="t",
            private_mode_confirmed=True,
        )
        self.assertEqual(ok.status, RouteStatus.PRIVATE)
        self.assertTrue(ok.external_call)

    def test_internal_public_needs_owner_consent(self) -> None:
        review = decide_route(classification=_C.INTERNAL, target=_T.PUBLIC, tenant_id="t")
        self.assertEqual(review.status, RouteStatus.HUMAN_REVIEW)
        self.assertFalse(review.external_call)
        self.assertEqual(review.required_permission, "owner_consent")
        consented = decide_route(
            classification=_C.INTERNAL, target=_T.PUBLIC, tenant_id="t", owner_consent=True
        )
        self.assertEqual(consented.status, RouteStatus.PUBLIC_MASKED)

    def test_secret_blocked_on_every_target(self) -> None:
        for target in (_T.LOCAL, _T.PRIVATE, _T.PUBLIC):
            d = decide_route(classification=_C.SECRET, target=target, tenant_id="t")
            self.assertEqual(d.status, RouteStatus.BLOCKED, target)
            self.assertFalse(d.external_call, target)

    def test_unknown_tenant_blocks_even_public_local(self) -> None:
        for tenant in ("", "   "):
            d = decide_route(classification=_C.PUBLIC, target=_T.LOCAL, tenant_id=tenant)
            self.assertEqual(d.status, RouteStatus.BLOCKED)
            self.assertFalse(d.external_call)

    def test_restricted_local_allowed(self) -> None:
        d = decide_route(classification=_C.RESTRICTED, target=_T.LOCAL, tenant_id="t")
        self.assertEqual(d.status, RouteStatus.LOCAL)
        self.assertTrue(d.allowed)
        self.assertFalse(d.external_call)

    def test_matrix_is_total_and_blocked_never_egresses(self) -> None:
        # Every (class, target) resolves; BLOCKED/HUMAN_REVIEW never permit egress,
        # and CONFIDENTIAL/RESTRICTED/SECRET never egress to PUBLIC (T1 invariant).
        for classification in _C:
            for target in _T:
                d = decide_route(classification=classification, target=target, tenant_id="t")
                if d.status in (RouteStatus.BLOCKED, RouteStatus.HUMAN_REVIEW):
                    self.assertFalse(d.external_call)
                if target is _T.PUBLIC and classification in (
                    _C.CONFIDENTIAL,
                    _C.RESTRICTED,
                    _C.SECRET,
                ):
                    self.assertEqual(d.status, RouteStatus.BLOCKED)


if __name__ == "__main__":
    unittest.main()
