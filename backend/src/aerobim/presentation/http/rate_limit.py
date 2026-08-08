"""Lightweight in-process HTTP rate limiting (RT-RATE-001)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

_RATE_LIMITED_PREFIXES = (
    "/v1/analyze/",
    "/v1/validate/",
    "/v1/uploads/",
)


class _SlidingWindowLimiter:
    def __init__(self, *, max_events: int, window_seconds: float) -> None:
        self._max_events = max_events
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        if self._max_events <= 0:
            return True
        now = time.monotonic()
        cutoff = now - self._window_seconds
        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self._max_events:
                return False
            bucket.append(now)
            return True


def add_rate_limit_middleware(app, *, requests_per_minute: int) -> None:  # noqa: ANN001
    """Attach per-client sliding-window limiter for expensive POST routes."""

    if requests_per_minute <= 0:
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response

    limiter = _SlidingWindowLimiter(max_events=requests_per_minute, window_seconds=60.0)

    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
            if request.method != "POST":
                return await call_next(request)
            path = request.url.path
            if not any(path.startswith(prefix) for prefix in _RATE_LIMITED_PREFIXES):
                return await call_next(request)
            client = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization", "")
            key = f"{client}:{auth[:32]}"
            if not limiter.allow(key):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
            return await call_next(request)

    app.add_middleware(_RateLimitMiddleware)


__all__ = ["add_rate_limit_middleware"]
