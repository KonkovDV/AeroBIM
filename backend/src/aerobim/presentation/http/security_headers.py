"""ASVS-aligned security headers for HTTP responses (OWASP ASVS 5.0 V3.4)."""

from __future__ import annotations

_STRICT_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
_HTML_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "frame-ancestors 'none'; base-uri 'none'"
)


def add_security_headers_middleware(app) -> None:  # noqa: ANN001
    """Attach middleware that sets nosniff / CSP / referrer / frame denial headers."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
            response: Response = await call_next(request)
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("Referrer-Policy", "no-referrer")
            response.headers.setdefault("X-Frame-Options", "DENY")
            content_type = (response.headers.get("content-type") or "").lower()
            if "text/html" in content_type:
                response.headers["Content-Security-Policy"] = _HTML_CSP
            else:
                response.headers.setdefault("Content-Security-Policy", _STRICT_CSP)
            return response

    app.add_middleware(_SecurityHeadersMiddleware)
