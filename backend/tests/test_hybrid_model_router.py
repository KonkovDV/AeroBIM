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

    def test_from_config_rejects_non_local_human_review(self) -> None:
        # Red Team MEDIUM: human_review profile must be LOCAL tier (review stays local).
        bad = copy.deepcopy(_CONFIG)
        bad["human_review_profile"] = "public_kimi_k3"
        with self.assertRaises(ValueError):
            ProviderRegistry.from_config(bad)

    def test_from_config_rejects_task_route_tier_mismatch(self) -> None:
        bad = copy.deepcopy(_CONFIG)
        bad["task_routes"]["local"] = {"x": "public_kimi_k3"}  # public profile in local slot
        with self.assertRaises(ValueError):
            ProviderRegistry.from_config(bad)

    def test_human_review_mistier_profile_yields_no_profile(self) -> None:
        # Red Team MEDIUM defense-in-depth: directly-built registry with a PUBLIC hr
        # profile must NOT hand out that profile under HUMAN_REVIEW.
        registry = ProviderRegistry(
            profiles={"pub": ModelProfile("pub", ModelTier.PUBLIC, "x", "y")},
            task_routes={},
            tier_defaults={},
            human_review_profile_name="pub",
        )
        sel = ModelRouter(registry).select(
            decision=_decide(_C.INTERNAL, _T.PUBLIC), task_type="drawing_read"
        )
        self.assertIsNone(sel.profile)
        self.assertTrue(sel.requires_human_review)
        self.assertFalse(sel.external)

    def test_di_router_available_and_local_only_by_default(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        container = bootstrap_container(Settings.from_env())
        router = container.resolve(Tokens.HYBRID_MODEL_ROUTER)
        self.assertIsInstance(router, ModelRouter)
        # LOCAL route -> local profile, no external egress.
        local = router.select(decision=_decide(_C.CONFIDENTIAL, _T.LOCAL), task_type="drawing_read")
        assert local.profile is not None
        self.assertIs(local.profile.tier, ModelTier.LOCAL)
        self.assertFalse(local.external)
        # PUBLIC route -> no public profile in the default registry -> fail-closed HR, no egress.
        public = router.select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="drawing_read")
        self.assertIsNone(public.profile)
        self.assertTrue(public.requires_human_review)
        self.assertFalse(public.external)


_FILE_CONFIG = {
    "profiles": {
        "local_vlm": {"tier": "local", "provider": "onprem", "model_id": "l"},
        "private_vlm": {"tier": "private", "provider": "ru", "model_id": "p"},
        "public_vlm": {"tier": "public", "provider": "pub", "model_id": "k"},
        "human_review": {"tier": "local", "provider": "human", "model_id": "e"},
    },
    "tier_defaults": {"local": "local_vlm", "private": "private_vlm", "public": "public_vlm"},
    "human_review_profile": "human_review",
}


class ModelRouterProviderConfigTests(unittest.TestCase):
    def _settings(self, path: str | None = None):  # noqa: ANN202
        from dataclasses import replace

        from aerobim.core.config.settings import Settings

        return replace(Settings.from_env(), hybrid_provider_config_path=path)

    def test_no_config_is_local_only_failclosed(self) -> None:
        from aerobim.infrastructure.di.bootstrap import _build_model_router

        router = _build_model_router(self._settings(None))
        pub = router.select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="drawing_read")
        self.assertFalse(pub.external)
        self.assertTrue(pub.requires_human_review)

    def test_config_file_enables_public_tier(self) -> None:
        import json
        import tempfile
        from pathlib import Path

        from aerobim.infrastructure.di.bootstrap import _build_model_router

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "providers.json"
            path.write_text(json.dumps(_FILE_CONFIG), encoding="utf-8")
            router = _build_model_router(self._settings(str(path)))
        pub = router.select(decision=_decide(_C.PUBLIC, _T.PUBLIC), task_type="drawing_read")
        assert pub.profile is not None
        self.assertTrue(pub.external)
        self.assertIs(pub.profile.tier, ModelTier.PUBLIC)

    def test_missing_config_path_fails_closed_loud(self) -> None:
        from aerobim.infrastructure.di.bootstrap import _build_model_router

        with self.assertRaises(RuntimeError):
            _build_model_router(self._settings("/nonexistent/does-not-exist.json"))

    def test_invalid_config_fails_closed_loud(self) -> None:
        import tempfile
        from pathlib import Path

        from aerobim.infrastructure.di.bootstrap import _build_model_router

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json"
            path.write_text("{ not json", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                _build_model_router(self._settings(str(path)))

    def test_empty_config_fails_closed(self) -> None:
        # Red Team LOW: empty {} would silently disable even local -> require profiles.
        import json
        import tempfile
        from pathlib import Path

        from aerobim.infrastructure.di.bootstrap import _build_model_router

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "empty.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                _build_model_router(self._settings(str(path)))

    def test_bootstrap_fails_loud_on_bad_provider_config(self) -> None:
        # Red Team MEDIUM: a set-but-missing config must fail at BOOT (eager resolve).
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        with self.assertRaises(RuntimeError):
            bootstrap_container(self._settings("/nonexistent/does-not-exist.json"))


if __name__ == "__main__":
    unittest.main()
