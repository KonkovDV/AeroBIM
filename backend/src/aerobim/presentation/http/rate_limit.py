"""Lightweight in-process HTTP rate limiting (RT-RATE-001)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

_RATE_LIMITED_POST_PREFIXES = (
    "/v1/analyze/",
    "/v1/validate/",
    "/v1/uploads/",
)
_JOB_POLL_PREFIX = "/v1/analyze/project-package/jobs/"
_DEFAULT_JOB_POLL_PER_MINUTE = 300


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


def add_rate_limit_middleware(
    app,  # noqa: ANN001
    *,
    requests_per_minute: int,
    job_poll_per_minute: int = 0,
) -> None:
    """Attach per-client sliding-window limiter for expensive routes."""

    if requests_per_minute <= 0 and job_poll_per_minute <= 0:
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response

    post_limiter = _SlidingWindowLimiter(
        max_events=requests_per_minute,
        window_seconds=60.0,
    )
    poll_limiter = _SlidingWindowLimiter(
        max_events=job_poll_per_minute,
        window_seconds=60.0,
    )

    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
            path = request.url.path
            client = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization", "")
            key = f"{client}:{auth[:32]}"

            if request.method == "GET" and path.startswith(_JOB_POLL_PREFIX):
                if job_poll_per_minute > 0 and not poll_limiter.allow(f"poll:{key}"):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
                return await call_next(request)

            if request.method != "POST":
                return await call_next(request)
            if not any(path.startswith(prefix) for prefix in _RATE_LIMITED_POST_PREFIXES):
                return await call_next(request)
            if requests_per_minute > 0 and not post_limiter.allow(f"post:{key}"):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
            return await call_next(request)

    app.add_middleware(_RateLimitMiddleware)


__all__ = ["_DEFAULT_JOB_POLL_PER_MINUTE", "add_rate_limit_middleware"]
