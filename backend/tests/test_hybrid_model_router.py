"""Hybrid AI P2: configurable model router — fail-closed, config-replaceable, no egress escalation.

Проверяет: выбор профиля по уже принятому маршруту (LOCAL/PRIVATE/PUBLIC_MASKED/
BLOCKED/HUMAN_REVIEW); внешний вызов только для PUBLIC; BLOCKED → нет профиля;
неизвестная (tier, task) → эскалация HUMAN_REVIEW; конфиг не может расширить egress
(отклонение при tier-mismatch и в from_config, и в самом роутере); смена модели =
смена конфига; детерминизм.
"""

from __future__ import annotations

import copy
import unittest

from aerobim.domain.hybrid import (
    DataClassification,
    ModelProfile,
    ModelRouter,
    ModelTier,
    ProviderRegistry,
    RouteTarget,
    decide_route,
)

_C = DataClassification
_T = RouteTarget

_CONFIG = {
    "profiles": {
        "local_vlm": {"tier": "local", "provider": "onprem", "model_id": "local-vlm-v1"},
        "private_vlm": {"tier": "private", "provider": "ru-cloud", "model_id": "private-vlm-v1"},
        "public_kimi_k3": {"tier": "public", "provider": "kimi", "model_id": "k3"},
        "public_control": {"tier": "public", "provider": "ctrl", "model_id": "ctrl-1"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "expert"},
    },
    "tier_defaults": {"local": "local_vlm", "private": "private_vlm", "public": "public_kimi_k3"},
    "task_routes": {"public": {"table_read": "public_control"}},
    "human_review_profile": "human_review",
}


def _router() -> ModelRouter:
    return ModelRouter(ProviderRegistry.from_config(_CONFIG))


def _decide(classification: DataClassification, target: RouteTarget):  # noqa: ANN202
    return decide_route(classification=classification, target=target, tenant_id="tenant-a")


class ModelRouterTests(unittest.TestCase):
    def test_local_route_selects_local_profile_no_egress(self) -> None:
        sel = _router().select(decision=_decide(_C.PUBLIC, _T.LOCAL), task_type="drawing_read")
        assert sel.profile is not None
        self.assertEqual(sel.profile.name, "local_vlm")
        self.assertIs(sel.profile.tier, ModelTier.LOCAL)
        self.assertFalse(sel.external)

    def test_private_route_no_egress(self) -> None:
        sel = _router().select(decision=_decide(_C.PUBLIC, _T.PRIVATE), task_type="drawing_read")
        assert sel.profile is not None
        self.assertEqual(sel.profile.name, "private_vlm")
        self.assertFalse(sel.external)

    def test_public_masked_default_profile_is_external(self) -> None:
        sel = _router().select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="drawing_read")
        assert sel.profile is not None
        self.assertEqual(sel.profile.name, "public_kimi_k3")
        self.assertTrue(sel.external)

    def test_task_route_overrides_tier_default(self) -> None:
        sel = _router().select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="table_read")
        assert sel.profile is not None
        self.assertEqual(sel.profile.name, "public_control")

    def test_blocked_route_has_no_profile(self) -> None:
        sel = _router().select(
            decision=_decide(_C.CONFIDENTIAL, _T.PUBLIC), task_type="drawing_read"
        )
        self.assertIsNone(sel.profile)
        self.assertFalse(sel.external)
        self.assertFalse(sel.requires_human_review)

    def test_human_review_route_never_external(self) -> None:
        sel = _router().select(decision=_decide(_C.INTERNAL, _T.PUBLIC), task_type="drawing_read")
        self.assertTrue(sel.requires_human_review)
        self.assertFalse(sel.external)

    def test_unmapped_tier_escalates_to_human_review(self) -> None:
        # Реестр без local-профиля/маршрута -> LOCAL-решение fail-closed в HUMAN_REVIEW.
        registry = ProviderRegistry.from_config(
            {
                "profiles": {"pub": {"tier": "public", "provider": "x", "model_id": "y"}},
                "tier_defaults": {"public": "pub"},
            }
        )
        sel = ModelRouter(registry).select(
            decision=_decide(_C.PUBLIC, _T.LOCAL), task_type="drawing_read"
        )
        self.assertIsNone(sel.profile)
        self.assertTrue(sel.requires_human_review)
        self.assertFalse(sel.external)

    def test_from_config_rejects_tier_mismatch(self) -> None:
        bad = copy.deepcopy(_CONFIG)
        bad["tier_defaults"]["local"] = "public_kimi_k3"  # public profile in local slot
        with self.assertRaises(ValueError):
            ProviderRegistry.from_config(bad)

    def test_router_guard_blocks_egress_escalation_on_direct_registry(self) -> None:
        # Реестр, собранный в обход from_config: local-слот указывает на PUBLIC-профиль.
        registry = ProviderRegistry(
            profiles={"bad": ModelProfile("bad", ModelTier.PUBLIC, "x", "y")},
            task_routes={},
            tier_defaults={ModelTier.LOCAL: "bad"},
        )
        sel = ModelRouter(registry).select(
            decision=_decide(_C.PUBLIC, _T.LOCAL), task_type="drawing_read"
        )
        self.assertIsNone(sel.profile)  # tier guard fires
        self.assertTrue(sel.requires_human_review)
        self.assertFalse(sel.external)

    def test_config_replaceable_without_core_change(self) -> None:
        swapped = copy.deepcopy(_CONFIG)
        swapped["profiles"]["public_kimi_k3"]["model_id"] = "k3-next"
        router = ModelRouter(ProviderRegistry.from_config(swapped))
        sel = router.select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="drawing_read")
        assert sel.profile is not None
        self.assertEqual(sel.profile.model_id, "k3-next")

    def test_selection_is_deterministic(self) -> None:
        router = _router()
        decision = _decide(_C.PUBLIC, _T.PUBLIC)
        first = router.select(decision=decision, task_type="drawing_read")
        second = router.select(decision=decision, task_type="drawing_read")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
