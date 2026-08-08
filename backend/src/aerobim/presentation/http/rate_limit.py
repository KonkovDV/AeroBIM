"""Lightweight HTTP rate limiting (RT-RATE-001) with optional Redis backend."""

from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aerobim.core.security.rate_limit_backend import RateLimitBackend
from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response

_RATE_LIMITED_POST_PREFIXES = (
    "/v1/analyze/",
    "/v1/validate/",
    "/v1/uploads/",
)
_JOB_POLL_PREFIX = "/v1/analyze/project-package/jobs/"
_DEFAULT_JOB_POLL_PER_MINUTE = 300
_WINDOW_SECONDS = 60.0


def add_rate_limit_middleware(
    app: FastAPI,
    *,
    requests_per_minute: int,
    job_poll_per_minute: int = 0,
    redis_url: str | None = None,
    signoff_profile: str = "development",
) -> None:
    """Attach per-client limiter for expensive routes (shared when Redis is configured)."""

    if requests_per_minute <= 0 and job_poll_per_minute <= 0:
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    backend: RateLimitBackend = build_rate_limit_backend(
        redis_url,
        signoff_profile=signoff_profile,
    )

    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            path = request.url.path
            client = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization", "")
            auth_fingerprint = (
                hashlib.sha256(auth.encode("utf-8")).hexdigest()[:16] if auth else "anon"
            )
            key = f"{client}:{auth_fingerprint}"

            if request.method == "GET" and path.startswith(_JOB_POLL_PREFIX):
                if job_poll_per_minute > 0 and not backend.allow(
                    bucket="poll",
                    key=key,
                    max_events=job_poll_per_minute,
                    window_seconds=_WINDOW_SECONDS,
                ):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
                response: Response = await call_next(request)
                return response

            if request.method != "POST":
                response = await call_next(request)
                return response
            if not any(path.startswith(prefix) for prefix in _RATE_LIMITED_POST_PREFIXES):
                response = await call_next(request)
                return response
            if requests_per_minute > 0 and not backend.allow(
                bucket="post",
                key=key,
                max_events=requests_per_minute,
                window_seconds=_WINDOW_SECONDS,
            ):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                )
            response = await call_next(request)
            return response

    app.add_middleware(_RateLimitMiddleware)


__all__ = ["_DEFAULT_JOB_POLL_PER_MINUTE", "add_rate_limit_middleware"]
