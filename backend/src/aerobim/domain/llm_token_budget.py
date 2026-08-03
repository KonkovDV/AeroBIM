"""Fail-closed token budget for advisory LLM calls (grant / repair-loop guard)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any


@dataclass
class LlmTokenBudget:
    """Process-local counters — not a distributed ledger; enough to stop runaway loops."""

    max_tokens_per_call: int = 4_096
    max_tokens_per_run: int = 500_000
    max_tokens_per_day: int = 2_000_000
    tokens_this_run: int = 0
    tokens_today: int = 0
    day_key: date = field(default_factory=lambda: datetime.now(tz=UTC).date())
    blocked_reason: str | None = None

    def _roll_day(self) -> None:
        today = datetime.now(tz=UTC).date()
        if today != self.day_key:
            self.day_key = today
            self.tokens_today = 0

    def check_before(self, *, estimated_tokens: int) -> str | None:
        """Return block reason or None if the call may proceed."""

        self._roll_day()
        if estimated_tokens <= 0:
            estimated_tokens = self.max_tokens_per_call
        if estimated_tokens > self.max_tokens_per_call:
            self.blocked_reason = "budget_exceeded:per_call"
            return self.blocked_reason
        if self.tokens_this_run + estimated_tokens > self.max_tokens_per_run:
            self.blocked_reason = "budget_exceeded:per_run"
            return self.blocked_reason
        if self.tokens_today + estimated_tokens > self.max_tokens_per_day:
            self.blocked_reason = "budget_exceeded:per_day"
            return self.blocked_reason
        return None

    def record(self, *, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
        self._roll_day()
        used = max(0, int(prompt_tokens)) + max(0, int(completion_tokens))
        self.tokens_this_run += used
        self.tokens_today += used
        return {
            "prompt_tokens": max(0, int(prompt_tokens)),
            "completion_tokens": max(0, int(completion_tokens)),
            "tokens_this_run": self.tokens_this_run,
            "tokens_today": self.tokens_today,
            "max_tokens_per_call": self.max_tokens_per_call,
            "max_tokens_per_run": self.max_tokens_per_run,
            "max_tokens_per_day": self.max_tokens_per_day,
            "day_key": self.day_key.isoformat(),
        }

    def snapshot(self) -> dict[str, Any]:
        self._roll_day()
        return {
            "tokens_this_run": self.tokens_this_run,
            "tokens_today": self.tokens_today,
            "max_tokens_per_call": self.max_tokens_per_call,
            "max_tokens_per_run": self.max_tokens_per_run,
            "max_tokens_per_day": self.max_tokens_per_day,
            "day_key": self.day_key.isoformat(),
            "blocked_reason": self.blocked_reason,
        }


__all__ = ["LlmTokenBudget"]
