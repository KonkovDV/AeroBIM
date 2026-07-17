"""Domain-level errors for capability degradation signalling."""

from __future__ import annotations


class ClashCapabilityError(RuntimeError):
    """Clash detection could not run; ``status`` is ``skipped`` or ``failed``."""

    def __init__(self, status: str, reason: str) -> None:
        if status not in {"skipped", "failed"}:
            raise ValueError(f"Invalid clash capability status: {status}")
        self.status = status
        self.reason = reason
        super().__init__(reason)


class HonestyCapabilityError(RuntimeError):
    """Honesty-gated capability illegally reported as delivered (e.g. OK)."""

    def __init__(self, capability: str, status: str, allowed: tuple[str, ...]) -> None:
        self.capability = capability
        self.status = status
        self.allowed = allowed
        super().__init__(
            f"Honesty capability {capability} has status {status!r}; allowed={list(allowed)}"
        )
