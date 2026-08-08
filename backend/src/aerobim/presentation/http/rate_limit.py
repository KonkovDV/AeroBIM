"""Lightweight HTTP rate limiting (RT-RATE-001) with optional Redis backend."""

from __future__ import annotations

from aerobim.core.security.rate_limit_backend import RateLimitBackend, build_rate_limit_backend

_RATE_LIMITED_POST_PREFIXES = (
    "/v1/analyze/",
    "/v1/validate/",
    "/v1/uploads/",
)
_JOB_POLL_PREFIX = "/v1/analyze/project-package/jobs/"
_DEFAULT_JOB_POLL_PER_MINUTE = 300
_WINDOW_SECONDS = 60.0


def add_rate_limit_middleware(
    app,  # noqa: ANN001
    *,
    requests_per_minute: int,
    job_poll_per_minute: int = 0,
    redis_url: str | None = None,
) -> None:
    """Attach per-client limiter for expensive routes (shared when Redis is configured)."""

    if requests_per_minute <= 0 and job_poll_per_minute <= 0:
        return

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response

    backend: RateLimitBackend = build_rate_limit_backend(redis_url)

    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
            path = request.url.path
            client = request.client.host if request.client else "unknown"
            auth = request.headers.get("authorization", "")
            key = f"{client}:{auth[:32]}"

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
                return await call_next(request)

            if request.method != "POST":
                return await call_next(request)
            if not any(path.startswith(prefix) for prefix in _RATE_LIMITED_POST_PREFIXES):
                return await call_next(request)
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
            return await call_next(request)

    app.add_middleware(_RateLimitMiddleware)


__all__ = ["_DEFAULT_JOB_POLL_PER_MINUTE", "add_rate_limit_middleware"]
