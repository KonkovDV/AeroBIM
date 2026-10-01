"""Hybrid AI P2: интеграционный стенд БЕЗ рабочего внешнего выхода.

Композирует весь контур end-to-end на синтетике: classify_object -> suggest_mask_rules
(детектор) -> HybridRouteGate (policy + маскирование + audit) -> ModelRouter (выбор
профиля). Доказывает агрегатные инварианты без единого сетевого вызова (всё
domain/application-pure): внешний выход (external egress) возможен ТОЛЬКО для класса
PUBLIC; чувствительные классы и неизвестный заказчик наружу не выходят; результат не
содержит вердикта (verdict-neutral). Это «стенд», а не рабочее подключение внешних моделей.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.domain.hybrid import (
    ModelRouter,
    PrivacyGuard,
    ProviderRegistry,
    RouteTarget,
    suggest_mask_rules,
)

_T = RouteTarget
_GID = "3n8vP2aQ9zXcVbNmLkJhG0"
_SECRET = "sk-abcdef0123456789xyz"

# Public-enabled router config (so external egress is POSSIBLE for a PUBLIC route).
_ROUTER_CONFIG = {
    "profiles": {
        "local_vlm": {"tier": "local", "provider": "onprem", "model_id": "l"},
        "private_vlm": {"tier": "private", "provider": "ru", "model_id": "p"},
        "public_vlm": {"tier": "public", "provider": "pub", "model_id": "k"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "e"},
    },
    "tier_defaults": {"local": "local_vlm", "private": "private_vlm", "public": "public_vlm"},
    "human_review_profile": "human_review",
}


def _run_flow(kind: str, target: RouteTarget, tenant: str, payload: dict | None):
    gate = HybridRouteGate(privacy_guard=PrivacyGuard(tenant_salt="bench-salt"))
    rules = suggest_mask_rules(payload, keep_clean_scalars=True) if payload else None
    result = gate.evaluate(
        object_kind=kind,
        target=target,
        tenant_id=tenant,
        task_type="drawing_read",
        request_id="bench",
        payload=payload,
        mask_rules=rules,
    )
    router = ModelRouter(ProviderRegistry.from_config(_ROUTER_CONFIG))
    selection = router.select(decision=result.decision, task_type="drawing_read")
    return result, selection


# (kind, target, tenant, payload, expect_classification)
_SCENARIOS = [
    ("ifc", _T.PUBLIC, "tenant-a", {"gid": _GID}, "confidential"),
    (
        "public_fixture",
        _T.PUBLIC,
        "tenant-a",
        {"q": "check", "gid": _GID, "api_key": _SECRET},
        "public",
    ),
    ("public_fixture", _T.PUBLIC, "", {"q": "x"}, "public"),  # unknown tenant
    ("customer_corpus", _T.LOCAL, "tenant-a", None, "restricted"),
    ("api_key", _T.PUBLIC, "tenant-a", {"x": "y"}, "secret"),
    ("ifc", _T.LOCAL, "tenant-a", None, "confidential"),
]


class HybridIntegrationBenchTests(unittest.TestCase):
    def test_external_egress_only_for_public_class_end_to_end(self) -> None:
        for kind, target, tenant, payload, cls in _SCENARIOS:
            result, selection = _run_flow(kind, target, tenant, payload)
            external = result.may_call_external and selection.external
            if external:
                self.assertEqual(cls, "public", (kind, target, tenant))
            # Sensitive classes / unknown tenant must never egress.
            if cls in {"confidential", "restricted", "secret"} or tenant.strip() == "":
                self.assertFalse(result.may_call_external, (kind, target, tenant))
                self.assertFalse(selection.external, (kind, target, tenant))

    def test_public_masked_egress_hides_raw_sensitive(self) -> None:
        result, selection = _run_flow(
            "public_fixture",
            _T.PUBLIC,
            "tenant-a",
            {"q": "check", "gid": _GID, "api_key": _SECRET},
        )
        self.assertTrue(result.may_call_external)
        self.assertTrue(selection.external)
        blob = json.dumps(result.masked)
        self.assertNotIn(_GID, blob)  # tokenized
        self.assertNotIn(_SECRET, blob)  # removed (detector -> remove for secret)
        self.assertEqual(result.masked["q"], "check")  # utility kept

    def test_flow_is_verdict_neutral(self) -> None:
        for kind, target, tenant, payload, _cls in _SCENARIOS:
            result, selection = _run_flow(kind, target, tenant, payload)
            self.assertFalse(hasattr(result, "passed"))
            self.assertFalse(hasattr(result, "summary"))
            self.assertFalse(hasattr(selection, "passed"))
            self.assertEqual(result.audit_event.verdict_impact, "none")

    def test_flow_is_deterministic(self) -> None:
        a = _run_flow("public_fixture", _T.PUBLIC, "tenant-a", {"gid": _GID})
        b = _run_flow("public_fixture", _T.PUBLIC, "tenant-a", {"gid": _GID})
        self.assertEqual(a[0].masked, b[0].masked)
        self.assertEqual(a[1], b[1])


if __name__ == "__main__":
    unittest.main()
