"""Lightweight HTTP rate limiting (RT-RATE-001) with optional Redis backend."""

from __future__ import annotations

import hashlib
import ipaddress
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from aerobim.core.security.rate_limit_backend import RateLimitBackend
from aerobim.infrastructure.security.rate_limit_factory import build_rate_limit_backend
from aerobim.presentation.http.security_headers import stamp_security_headers

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response

_RATE_LIMITED_POST_PREFIXES = (
    "/v1/analyze/",
    "/v1/validate/",
    "/v1/uploads/",
)
_RATE_LIMITED_GET_EXACT = (
    "/v1/auth/login",
    "/v1/auth/callback",
    "/v1/auth/session",
)
_JOB_POLL_PREFIX = "/v1/analyze/project-package/jobs/"
_DEFAULT_JOB_POLL_PER_MINUTE = 300
_WINDOW_SECONDS = 60.0
_RETRY_AFTER = str(int(_WINDOW_SECONDS))


def client_bucket_host(request: Request, trusted_proxy_ips: frozenset[str]) -> str:
    """Peer IP, or first X-Forwarded-For hop when the peer is a configured proxy."""

    peer = request.client.host if request.client else "unknown"
    if not trusted_proxy_ips or peer not in trusted_proxy_ips:
        return peer
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if not forwarded or "/" in forwarded or any(ch.isspace() for ch in forwarded):
        return peer
    try:
        return str(ipaddress.ip_address(forwarded))
    except ValueError:
        return peer


def _limited_response(*, path: str) -> Response:
    from starlette.responses import JSONResponse

    return stamp_security_headers(
        JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": _RETRY_AFTER},
        ),
        path=path,
    )


def add_rate_limit_middleware(
    app: FastAPI,
    *,
    requests_per_minute: int,
    job_poll_per_minute: int = 0,
    redis_url: str | None = None,
    signoff_profile: str = "development",
    fail_closed: bool = False,
    trusted_proxy_ips: tuple[str, ...] = (),
) -> None:
    """Attach per-client limiter for expensive routes (shared when Redis is configured)."""

    if requests_per_minute <= 0 and job_poll_per_minute <= 0:
        return

    from starlette.middleware.base import BaseHTTPMiddleware

    backend: RateLimitBackend = build_rate_limit_backend(
        redis_url,
        signoff_profile=signoff_profile,
        fail_closed=fail_closed,
    )
    trusted = frozenset(ip.strip() for ip in trusted_proxy_ips if ip.strip())

    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            path = request.url.path
            client = client_bucket_host(request, trusted)
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
                    return _limited_response(path=path)
                response: Response = await call_next(request)
                return response

            if request.method == "GET" and path in _RATE_LIMITED_GET_EXACT:
                if requests_per_minute > 0 and not backend.allow(
                    bucket="auth-get",
                    key=key,
                    max_events=requests_per_minute,
                    window_seconds=_WINDOW_SECONDS,
                ):
                    return _limited_response(path=path)
                response = await call_next(request)
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
                return _limited_response(path=path)
            response = await call_next(request)
            return response

    app.add_middleware(_RateLimitMiddleware)


__all__ = [
    "_DEFAULT_JOB_POLL_PER_MINUTE",
    "add_rate_limit_middleware",
    "client_bucket_host",
]
