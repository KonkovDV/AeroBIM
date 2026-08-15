"""ASVS-aligned security headers for HTTP responses (OWASP ASVS 5.0 V3.4)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response

_STRICT_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_HTML_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "frame-ancestors 'none'; base-uri 'none'"
)
_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=()"
_HSTS = "max-age=31536000; includeSubDomains"
_MAX_AUTHORIZATION_HEADER_BYTES = 8192


def add_auth_header_hygiene_middleware(app: FastAPI) -> None:
    """Reject duplicate / oversized / smuggled Authorization headers before auth."""

    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import JSONResponse

    class _AuthHeaderHygieneMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            values = request.headers.getlist("authorization")
            if len(values) > 1:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid Authorization header"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if values:
                raw = values[0]
                if len(raw.encode("utf-8")) > _MAX_AUTHORIZATION_HEADER_BYTES:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid Authorization header"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                if raw.lower().count("bearer ") > 1:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid Authorization header"},
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            return await call_next(request)

    app.add_middleware(_AuthHeaderHygieneMiddleware)


def add_security_headers_middleware(app: FastAPI) -> None:
    """Attach middleware that sets ASVS-aligned browser hardening headers."""
    from starlette.middleware.base import BaseHTTPMiddleware

    class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            response: Response = await call_next(request)
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("Permissions-Policy", _PERMISSIONS_POLICY)
            response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
            response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
            # Harmless on HTTP; required when TLS terminates at the app or a proxy that
            # forwards this response. Reverse proxies may override.
            response.headers.setdefault("Strict-Transport-Security", _HSTS)
            path = request.url.path or ""
            if path.startswith("/v1/") or path in {"/health", "/ready", "/metrics"}:
                response.headers.setdefault("Cache-Control", "no-store")
            content_type = (response.headers.get("content-type") or "").lower()
            if "text/html" in content_type:
                response.headers["Content-Security-Policy"] = _HTML_CSP
            else:
                response.headers.setdefault("Content-Security-Policy", _STRICT_CSP)
            return response

    app.add_middleware(_SecurityHeadersMiddleware)
