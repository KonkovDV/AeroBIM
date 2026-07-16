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
