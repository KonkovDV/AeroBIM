"""Rate-limit backend protocol (in-process or Redis-shared)."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Protocol

_logger = logging.getLogger(__name__)


class RateLimitBackend(Protocol):
    def allow(self, *, bucket: str, key: str, max_events: int, window_seconds: float) -> bool: ...


class InProcessRateLimitBackend:
    """Per-process sliding window (dev / single-replica fallback)."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, *, bucket: str, key: str, max_events: int, window_seconds: float) -> bool:
        if max_events <= 0:
            return True
        composite = f"{bucket}:{key}"
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[composite]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= max_events:
                return False
            events.append(now)
            return True


def build_rate_limit_backend(redis_url: str | None) -> RateLimitBackend:
    """Prefer Redis when configured; fall back to in-process on import/connect errors."""

    if not redis_url:
        return InProcessRateLimitBackend()
    try:
        from aerobim.infrastructure.security.redis_rate_limiter import RedisRateLimitBackend

        return RedisRateLimitBackend(redis_url)
    except Exception as exc:  # noqa: BLE001 — degrade to local limiter
        _logger.warning(
            "Redis rate limiter unavailable; using in-process limiter: %s",
            exc,
        )
        return InProcessRateLimitBackend()


__all__ = [
    "InProcessRateLimitBackend",
    "RateLimitBackend",
    "build_rate_limit_backend",
]
