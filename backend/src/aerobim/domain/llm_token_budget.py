"""Fail-closed token budget for advisory LLM calls (grant / repair-loop guard)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Default IANA zone for day roll (back-compat). Override via AEROBIM_LLM_BUDGET_TZ
# when the team plans spend in a local calendar day (e.g. Europe/Moscow).
_DEFAULT_BUDGET_TZ = "UTC"


@dataclass
class LlmTokenBudget:
    """In-memory counters. File-backed variant lives in infrastructure (I7)."""

    max_tokens_per_call: int = 4_096
    max_tokens_per_run: int = 500_000
    max_tokens_per_day: int = 2_000_000
    tokens_this_run: int = 0
    tokens_today: int = 0
    day_key: date = field(default_factory=lambda: datetime.now(tz=UTC).date())
    blocked_reason: str | None = None
    budget_tz: str = _DEFAULT_BUDGET_TZ
    budget_scope: str = "process_local"
    lock_degraded: bool = False
    """Set by file-backed adapter when cross-process lock cannot be held (RT-LEDGER-01)."""

    def _zone(self) -> ZoneInfo | Any:
        try:
            return ZoneInfo(self.budget_tz or _DEFAULT_BUDGET_TZ)
        except ZoneInfoNotFoundError:
            return UTC

    def _today(self) -> date:
        return datetime.now(tz=self._zone()).date()

    def _roll_day(self) -> None:
        today = self._today()
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
        self.blocked_reason = None
        return self.snapshot(include_last_charge=used)

    def record_failed(self, *, estimated_tokens: int) -> dict[str, Any]:
        """Conservative charge when transport fails after possible vendor billing.

        Mirrors the omit-usage path: provider may have billed tokens we never saw
        (RT-BUDGET-01). Caps at ``max_tokens_per_call``.
        """

        self._roll_day()
        used = max(0, int(estimated_tokens))
        if used <= 0:
            used = self.max_tokens_per_call
        used = min(used, self.max_tokens_per_call)
        self.tokens_this_run += used
        self.tokens_today += used
        return self.snapshot(include_last_charge=used)

    def apply_persisted_day(self, *, day_key: date, tokens_today: int) -> None:
        """Hydrate day counters from an infrastructure store (domain stays I/O-free)."""

        self.day_key = day_key
        self.tokens_today = max(0, int(tokens_today))
        self._roll_day()

    def snapshot(self, *, include_last_charge: int | None = None) -> dict[str, Any]:
        self._roll_day()
        out: dict[str, Any] = {
            "tokens_this_run": self.tokens_this_run,
            "tokens_today": self.tokens_today,
            "max_tokens_per_call": self.max_tokens_per_call,
            "max_tokens_per_run": self.max_tokens_per_run,
            "max_tokens_per_day": self.max_tokens_per_day,
            "day_key": self.day_key.isoformat(),
            "budget_tz": self.budget_tz,
            "budget_scope": self.budget_scope,
            "lock_degraded": bool(self.lock_degraded),
            "blocked_reason": self.blocked_reason,
        }
        if include_last_charge is not None:
            out["last_charge_tokens"] = include_last_charge
        return out


__all__ = ["LlmTokenBudget"]
