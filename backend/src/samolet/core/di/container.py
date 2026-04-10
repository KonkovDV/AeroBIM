from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


Factory = Callable[["Container"], Any]


class Lifecycle(StrEnum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"


@dataclass
class Registration:
    factory: Factory
    lifecycle: Lifecycle = Lifecycle.SINGLETON
    instance: Any | None = None


class Container:
    def __init__(self) -> None:
        self._registrations: dict[str, Registration] = {}

    def register(
        self,
        token: str,
        factory: Factory,
        lifecycle: Lifecycle = Lifecycle.SINGLETON,
    ) -> None:
        if token in self._registrations:
            raise ValueError(f"Token is already registered: {token}")
        self._registrations[token] = Registration(factory=factory, lifecycle=lifecycle)

    def resolve(self, token: str) -> Any:
        registration = self._registrations.get(token)
        if registration is None:
            raise KeyError(f"Token is not registered: {token}")

        if registration.lifecycle is Lifecycle.SINGLETON:
            if registration.instance is None:
                registration.instance = registration.factory(self)
            return registration.instance

        return registration.factory(self)

    def is_registered(self, token: str) -> bool:
        return token in self._registrations

    def registered_tokens(self) -> tuple[str, ...]:
        return tuple(self._registrations)
