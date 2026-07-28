"""Hybrid AI P0.8: typed audit event — full path, secret-safe, verdict-neutral.

Verifies §13/§25: the event captures the route path; forbidden (secret) keys are
redacted and the serializer fails closed; verdict_impact is always "none" and cannot
be overridden via metadata; the content hash is tamper-evident.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.hybrid import (
    AuditSecretLeakError,
    DataClassification,
    RouteTarget,
    build_route_audit_event,
    decide_route,
    redact_audit_fields,
)
from aerobim.domain.hybrid.audit_event import _assert_no_forbidden_keys

_C = DataClassification
_T = RouteTarget


def _event(decision, **meta):  # noqa: ANN001, ANN003 — test helper
    return build_route_audit_event(
        event_id="e1",
        timestamp="2026-07-28T00:00:00Z",
        request_id="req-1",
        tenant_id="tenant-a",
        task_type="drawing_read",
        decision=decision,
        **meta,
    )


class HybridAuditEventTests(unittest.TestCase):
    def test_blocked_decision_maps_to_none_tier_with_reason(self) -> None:
        decision = decide_route(
            classification=_C.CONFIDENTIAL, target=_T.PUBLIC, tenant_id="tenant-a"
        )
        event = _event(decision)
        self.assertEqual(event.route_status, "blocked")
        self.assertEqual(event.tier, "none")
        self.assertFalse(event.human_review_required)
        self.assertIsNotNone(event.failure_reason)
        self.assertEqual(event.verdict_impact, "none")

    def test_public_masked_maps_to_public_tier(self) -> None:
        decision = decide_route(classification=_C.PUBLIC, target=_T.PUBLIC, tenant_id="tenant-a")
        event = _event(decision)
        self.assertEqual(event.route_status, "public_masked")
        self.assertEqual(event.tier, "public")
        self.assertIsNone(event.failure_reason)

    def test_human_review_flagged(self) -> None:
        decision = decide_route(classification=_C.INTERNAL, target=_T.PUBLIC, tenant_id="tenant-a")
        event = _event(decision)
        self.assertEqual(event.route_status, "human_review")
        self.assertTrue(event.human_review_required)

    def test_metadata_cannot_override_verdict_impact_or_route(self) -> None:
        decision = decide_route(classification=_C.PUBLIC, target=_T.LOCAL, tenant_id="tenant-a")
        event = _event(decision, verdict_impact="tampered", route_status="pass")
        self.assertEqual(event.verdict_impact, "none")  # fixed by construction
        self.assertEqual(event.route_status, "local")  # from decision, not metadata

    def test_redact_audit_fields_strips_secrets_recursively(self) -> None:
        safe = redact_audit_fields(
            {
                "prompt_tokens": 10,
                "api_key": "sk-should-be-gone",
                "nested": {"Authorization": "Bearer x", "ok": 1},
                "reasoning_content": "chain-of-thought",
            }
        )
        self.assertEqual(safe, {"prompt_tokens": 10, "nested": {"ok": 1}})

    def test_to_audit_dict_redacts_usage_and_is_json_safe(self) -> None:
        decision = decide_route(classification=_C.PUBLIC, target=_T.PUBLIC, tenant_id="tenant-a")
        event = _event(
            decision,
            usage={"prompt_tokens": 5, "api_key": "sk-leak", "reasoning_content": "cot"},
            model_id="kimi-k3",
            response_hash="deadbeef",
        )
        record = event.to_audit_dict()
        self.assertNotIn("api_key", record["usage"])
        self.assertNotIn("reasoning_content", record["usage"])
        self.assertEqual(record["usage"]["prompt_tokens"], 5)
        # Whole record is JSON-serializable and has no forbidden key at any depth.
        json.dumps(record)

    def test_serializer_fails_closed_on_planted_secret(self) -> None:
        with self.assertRaises(AuditSecretLeakError):
            _assert_no_forbidden_keys({"tenant_id": "t", "token": "leak"})
        with self.assertRaises(AuditSecretLeakError):
            _assert_no_forbidden_keys({"usage": {"nested": {"password": "leak"}}})

    def test_content_hash_is_tamper_evident(self) -> None:
        decision = decide_route(classification=_C.PUBLIC, target=_T.LOCAL, tenant_id="tenant-a")
        base = _event(decision, response_hash="aaaa")
        same = _event(decision, response_hash="aaaa")
        changed = _event(decision, response_hash="bbbb")
        self.assertEqual(base.event_content_hash(), same.event_content_hash())
        self.assertNotEqual(base.event_content_hash(), changed.event_content_hash())


if __name__ == "__main__":
    unittest.main()
