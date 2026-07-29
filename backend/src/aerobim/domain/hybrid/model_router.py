"""Configurable model router (P2, domain-pure): pick a MODEL PROFILE for an
already-decided route (маршрутизатор моделей).

Провайдер-независимый (provider-agnostic): без SDK, без сети. Маршрут
(LOCAL/PRIVATE/PUBLIC_MASKED/…) решается ВЫШЕ, в :func:`trust_policy.decide_route`;
роутер только выбирает, КАКОЙ профиль модели обслуживает этот маршрут, из
**конфигурируемого реестра** — поэтому смена модели/провайдера = изменение конфига,
а НЕ изменение детерминированного расчётного ядра.

Least privilege / fail-closed:
- решение не разрешено (BLOCKED) → профиль не выбирается;
- HUMAN_REVIEW → профиль экспертной проверки, без внешнего вызова;
- нет настроенного профиля для (tier, task) → эскалация в HUMAN_REVIEW (не молча);
- профиль, чей tier ПРЕВЫШАЕТ tier принятого маршрута, ОТКЛОНЯЕТСЯ (конфиг не может
  расширить внешний выход) → HUMAN_REVIEW.

Модель не выбирает маршрут; роутер не может его расширить.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from aerobim.domain.hybrid.trust_policy import RouteDecision, RouteStatus


class ModelTier(Enum):
    """Уровень исполнения модели (совпадает с разрешённым маршрутом)."""

    LOCAL = "local"
    PRIVATE = "private"
    PUBLIC = "public"


_STATUS_TIER: dict[RouteStatus, ModelTier] = {
    RouteStatus.LOCAL: ModelTier.LOCAL,
    RouteStatus.PRIVATE: ModelTier.PRIVATE,
    RouteStatus.PUBLIC_MASKED: ModelTier.PUBLIC,
}


@dataclass(frozen=True)
class ModelProfile:
    """Провайдер-независимое описание модели (без SDK/сети)."""

    name: str
    tier: ModelTier
    provider: str
    model_id: str
    deterministic: bool = False


@dataclass(frozen=True)
class ModelSelection:
    """Результат выбора: профиль (или None) + причина + флаги."""

    profile: ModelProfile | None
    reason: str
    requires_human_review: bool = False

    @property
    def external(self) -> bool:
        """Внешний вызов только для PUBLIC-профиля и никогда при HUMAN_REVIEW."""
        return (
            self.profile is not None
            and self.profile.tier is ModelTier.PUBLIC
            and not self.requires_human_review
        )


class ProviderRegistry:
    """Конфигурируемый реестр профилей (config → профили + маршруты)."""

    def __init__(
        self,
        *,
        profiles: Mapping[str, ModelProfile],
        task_routes: Mapping[tuple[ModelTier, str], str],
        tier_defaults: Mapping[ModelTier, str],
        human_review_profile_name: str | None = None,
    ) -> None:
        self._profiles = dict(profiles)
        self._task_routes = dict(task_routes)
        self._tier_defaults = dict(tier_defaults)
        self._hr_name = human_review_profile_name

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> ProviderRegistry:
        """Собрать реестр из конфига; fail-closed на несогласованности tier."""
        profiles: dict[str, ModelProfile] = {}
        for name, spec in dict(config.get("profiles", {})).items():
            profiles[str(name)] = ModelProfile(
                name=str(name),
                tier=ModelTier(str(spec["tier"]).lower()),
                provider=str(spec["provider"]),
                model_id=str(spec["model_id"]),
                deterministic=bool(spec.get("deterministic", False)),
            )

        def _check(profile_name: str, tier: ModelTier, where: str) -> None:
            prof = profiles.get(profile_name)
            if prof is None:
                raise ValueError(f"{where}: unknown profile {profile_name!r}")
            if prof.tier is not tier:
                raise ValueError(
                    f"{where}: profile {profile_name!r} tier {prof.tier.value} "
                    f"!= slot {tier.value} (config cannot escalate egress)"
                )

        tier_defaults: dict[ModelTier, str] = {}
        for tkey, pname in dict(config.get("tier_defaults", {})).items():
            tier = ModelTier(str(tkey).lower())
            _check(str(pname), tier, "tier_defaults")
            tier_defaults[tier] = str(pname)

        task_routes: dict[tuple[ModelTier, str], str] = {}
        for tkey, tasks in dict(config.get("task_routes", {})).items():
            tier = ModelTier(str(tkey).lower())
            for task, pname in dict(tasks).items():
                _check(str(pname), tier, "task_routes")
                task_routes[(tier, str(task))] = str(pname)

        hr = config.get("human_review_profile")
        if hr is not None:
            if str(hr) not in profiles:
                raise ValueError(f"human_review_profile references unknown profile {hr!r}")
            if profiles[str(hr)].tier is not ModelTier.LOCAL:
                raise ValueError(
                    f"human_review_profile {hr!r} must be LOCAL tier (review stays local)"
                )

        return cls(
            profiles=profiles,
            task_routes=task_routes,
            tier_defaults=tier_defaults,
            human_review_profile_name=(str(hr) if hr is not None else None),
        )

    def resolve(self, tier: ModelTier, task_type: str) -> ModelProfile | None:
        name = self._task_routes.get((tier, task_type)) or self._tier_defaults.get(tier)
        return self._profiles.get(name) if name is not None else None

    def human_review_profile(self) -> ModelProfile | None:
        return self._profiles.get(self._hr_name) if self._hr_name is not None else None


class ModelRouter:
    """Выбор профиля модели для уже принятого маршрута (config-replaceable)."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def select(self, *, decision: RouteDecision, task_type: str) -> ModelSelection:
        if decision.status is RouteStatus.HUMAN_REVIEW:
            hr_profile = self._registry.human_review_profile()
            if hr_profile is not None and hr_profile.tier is not ModelTier.LOCAL:
                # Defense-in-depth: never hand out a non-local profile for HR, even if
                # a directly-built registry bypassed from_config validation.
                hr_profile = None
            return ModelSelection(
                profile=hr_profile,
                reason="human review required",
                requires_human_review=True,
            )
        if not decision.allowed:  # BLOCKED
            return ModelSelection(
                profile=None,
                reason=f"route blocked: {decision.reason}",
                requires_human_review=False,
            )
        tier = _STATUS_TIER.get(decision.status)
        if tier is None:
            return ModelSelection(
                profile=None, reason="no model tier for route", requires_human_review=True
            )
        profile = self._registry.resolve(tier, task_type)
        if profile is None:
            return ModelSelection(
                profile=None,
                reason=f"no configured model for {tier.value}/{task_type}",
                requires_human_review=True,
            )
        if profile.tier is not tier:
            # Defense-in-depth: a registry built directly (bypassing from_config)
            # must still never escalate egress beyond the decided route tier.
            return ModelSelection(
                profile=None,
                reason="profile tier exceeds route tier",
                requires_human_review=True,
            )
        return ModelSelection(profile=profile, reason=f"selected {profile.name}")


__all__ = [
    "ModelProfile",
    "ModelRouter",
    "ModelSelection",
    "ModelTier",
    "ProviderRegistry",
]
