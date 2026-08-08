"""Request correlation middleware for FastAPI.

Implements the W3C Trace Context pattern: each HTTP request gets a unique
correlation_id (from X-Request-ID header or auto-generated UUID4).
The ID is propagated via contextvars and injected into all response headers.
"""

from __future__ import annotations

import contextvars
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response

_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

HEADER_NAME = "X-Request-ID"


def get_correlation_id() -> str:
    """Return the current request's correlation ID (empty outside request scope)."""
    return _correlation_id.get()


def add_correlation_middleware(app: FastAPI) -> None:
    """Attach ASGI middleware that sets and propagates correlation IDs."""
    from starlette.middleware.base import BaseHTTPMiddleware

    class _CorrelationMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            incoming_id = request.headers.get(HEADER_NAME, "")
            cid = incoming_id or uuid4().hex
            token = _correlation_id.set(cid)
            try:
                response: Response = await call_next(request)
                response.headers[HEADER_NAME] = cid
                return response
            finally:
                _correlation_id.reset(token)

    app.add_middleware(_CorrelationMiddleware)
