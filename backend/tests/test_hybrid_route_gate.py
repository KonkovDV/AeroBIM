"""Hybrid AI P1-wire: HybridRouteGate end-to-end fail-closed + verdict-neutral (§16).

Composes classification + policy + masking + audit into one gate and proves the
brief §16 invariants at the integration level: forbidden classes / unknown tenant
never egress; external egress requires masking (fail-closed without a guard); the
gate carries NO verdict; and the DI-registered gate is available but verdict-neutral.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.domain.hybrid import PrivacyGuard, RouteStatus, RouteTarget

_T = RouteTarget


def _gate(*, with_guard: bool = False) -> HybridRouteGate:
    guard = PrivacyGuard(tenant_salt="deploy-salt") if with_guard else None
    return HybridRouteGate(privacy_guard=guard)


class HybridRouteGateTests(unittest.TestCase):
    def _eval(self, gate: HybridRouteGate, **kw: object):  # noqa: ANN003
        base: dict[str, object] = {
            "tenant_id": "tenant-a",
            "task_type": "drawing_read",
            "request_id": "req-1",
            "timestamp": "2026-07-28T00:00:00Z",
            "event_id": "e1",
        }
        base.update(kw)
        return gate.evaluate(**base)  # type: ignore[arg-type]

    def test_confidential_public_blocked_no_egress(self) -> None:
        r = self._eval(_gate(), object_kind="ifc", target=_T.PUBLIC)
        self.assertEqual(r.decision.status, RouteStatus.BLOCKED)
        self.assertIsNone(r.masked)
        self.assertFalse(r.may_call_external)
        self.assertEqual(r.audit_event.tier, "none")
        self.assertEqual(r.audit_event.verdict_impact, "none")

    def test_restricted_public_blocked(self) -> None:
        r = self._eval(_gate(), object_kind="customer_corpus", target=_T.PUBLIC)
        self.assertEqual(r.decision.status, RouteStatus.BLOCKED)
        self.assertFalse(r.may_call_external)

    def test_secret_blocked_on_all_targets(self) -> None:
        for target in (_T.LOCAL, _T.PRIVATE, _T.PUBLIC):
            r = self._eval(_gate(), object_kind="api_key", target=target)
            self.assertEqual(r.decision.status, RouteStatus.BLOCKED, target)
            self.assertFalse(r.may_call_external, target)

    def test_unknown_tenant_blocked(self) -> None:
        r = self._eval(_gate(), object_kind="public_fixture", target=_T.PUBLIC, tenant_id="")
        self.assertEqual(r.decision.status, RouteStatus.BLOCKED)
        self.assertFalse(r.may_call_external)

    def test_public_masked_egress_with_guard(self) -> None:
        r = self._eval(
            _gate(with_guard=True),
            object_kind="public_fixture",
            target=_T.PUBLIC,
            payload={"q": "check thickness", "gid": "GID-SECRET-1"},
            mask_rules={"q": "keep", "gid": "tokenize:global_id"},
        )
        self.assertEqual(r.decision.status, RouteStatus.PUBLIC_MASKED)
        self.assertIsNotNone(r.masked)
        self.assertTrue(r.may_call_external)
        self.assertNotIn("GID-SECRET-1", json.dumps(r.masked))
        self.assertIn("gid", r.audit_event.fields_sent)
        self.assertEqual(r.audit_event.mask_version, "1.0.0")

    def test_egress_without_guard_is_failclosed(self) -> None:
        # Policy-eligible for public egress, but no guard/rules -> must NOT send.
        r = self._eval(
            _gate(with_guard=False),
            object_kind="public_fixture",
            target=_T.PUBLIC,
            payload={"gid": "GID-SECRET"},
        )
        self.assertEqual(r.decision.status, RouteStatus.PUBLIC_MASKED)
        self.assertIsNone(r.masked)
        self.assertFalse(r.may_call_external)

    def test_question_only_egress_allowed(self) -> None:
        r = self._eval(_gate(), object_kind="public_fixture", target=_T.PUBLIC, payload=None)
        self.assertEqual(r.masked, {})
        self.assertTrue(r.may_call_external)

    def test_local_processing_allowed_no_egress(self) -> None:
        r = self._eval(_gate(), object_kind="ifc", target=_T.LOCAL)
        self.assertEqual(r.decision.status, RouteStatus.LOCAL)
        self.assertTrue(r.decision.allowed)
        self.assertFalse(r.may_call_external)
        self.assertIsNone(r.masked)

    def test_result_carries_no_verdict(self) -> None:
        r = self._eval(_gate(), object_kind="ifc", target=_T.PUBLIC)
        self.assertFalse(hasattr(r, "passed"))
        self.assertFalse(hasattr(r, "summary"))
        self.assertEqual(r.audit_event.verdict_impact, "none")

    def test_egress_refusal_is_audited_distinct_from_question_only(self) -> None:
        # Red Team MEDIUM-1: a fail-closed refusal must be distinguishable in the audit.
        refusal = self._eval(
            _gate(with_guard=False),
            object_kind="public_fixture",
            target=_T.PUBLIC,
            payload={"gid": "GID-SECRET"},
        )
        self.assertIsNone(refusal.masked)
        self.assertFalse(refusal.may_call_external)
        self.assertIn("fail-closed", refusal.audit_event.failure_reason or "")
        # Question-only egress: no refusal reason.
        question = self._eval(_gate(), object_kind="public_fixture", target=_T.PUBLIC, payload=None)
        self.assertEqual(question.masked, {})
        self.assertTrue(question.may_call_external)
        self.assertIsNone(question.audit_event.failure_reason)

    def test_masking_leak_refusal_is_audited(self) -> None:
        # Red Team MEDIUM-2: a masking failure (leak) must fail-closed AND be audited.
        r = self._eval(
            _gate(with_guard=True),
            object_kind="public_fixture",
            target=_T.PUBLIC,
            payload={"gid": "GID-SECRET", "note": "see GID-SECRET"},
            mask_rules={"gid": "tokenize:global_id", "note": "keep"},
        )
        self.assertIsNone(r.masked)
        self.assertFalse(r.may_call_external)
        self.assertIn("masking refused", r.audit_event.failure_reason or "")

    def test_human_review_no_egress(self) -> None:
        r = self._eval(_gate(), object_kind="internal_doc", target=_T.PUBLIC)
        self.assertEqual(r.decision.status, RouteStatus.HUMAN_REVIEW)
        self.assertFalse(r.may_call_external)
        self.assertEqual(r.audit_event.tier, "none")

    def test_di_gate_available_and_verdict_neutral(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        container = bootstrap_container(Settings.from_env())
        gate = container.resolve(Tokens.HYBRID_ROUTE_GATE)
        self.assertIsInstance(gate, HybridRouteGate)
        # DI gate is mask-less -> confidential public blocked; external egress fail-closed.
        result = gate.evaluate(
            object_kind="ifc",
            target=_T.PUBLIC,
            tenant_id="tenant-a",
            task_type="drawing_read",
            request_id="req-di",
        )
        self.assertEqual(result.decision.status, RouteStatus.BLOCKED)
        self.assertFalse(result.may_call_external)


if __name__ == "__main__":
    unittest.main()
