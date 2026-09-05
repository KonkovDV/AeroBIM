"""Rate-limit backend protocol (in-process or Redis-shared)."""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from threading import Lock
from typing import Protocol

DEFAULT_MAX_KEYS = 4096


class RateLimitBackend(Protocol):
    def allow(self, *, bucket: str, key: str, max_events: int, window_seconds: float) -> bool: ...


class InProcessRateLimitBackend:
    """Per-process sliding window (dev / single-replica fallback).

    HD2-RL-01: Redis backend is fixed-window; do not treat in-process tests as
    covering Redis boundary burst behaviour.

    RL-01: ``max_keys`` caps distinct bucket:key entries (LRU eviction) so a
    token-spray cannot grow this dict without bound.
    """

    def __init__(self, *, max_keys: int = DEFAULT_MAX_KEYS) -> None:
        if max_keys < 1:
            raise ValueError("max_keys must be >= 1")
        self._max_keys = max_keys
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = Lock()

    def allow(self, *, bucket: str, key: str, max_events: int, window_seconds: float) -> bool:
        # HD2-RL-02: 0 = limiter off (by design in development). Pilot/production
        # reject <=0 at Settings boot; do not treat this branch as a silent prod disable.
        if max_events <= 0:
            return True
        composite = f"{bucket}:{key}"
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events.get(composite)
            if events is None:
                self._evict_if_needed_unlocked()
                events = deque()
                self._events[composite] = events
            else:
                self._events.move_to_end(composite)
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= max_events:
                return False
            events.append(now)
            return True

    def _evict_if_needed_unlocked(self) -> None:
        while len(self._events) >= self._max_keys:
            self._events.popitem(last=False)


__all__ = [
    "DEFAULT_MAX_KEYS",
    "InProcessRateLimitBackend",
    "RateLimitBackend",
]
