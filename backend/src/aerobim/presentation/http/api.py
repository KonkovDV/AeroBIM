# pyright: reportUnusedFunction=false, reportUnknownVariableType=false

"""HTTP composition root.

Route handlers live in ``presentation/http/routes/*`` as APIRouter factories;
shared per-app dependencies (auth, path jail, ACL, serializers) live in
``presentation/http/context.ApiContext``. This module only wires middleware
and includes the routers, keeping the historical public surface:
``create_http_app`` and ``_esc``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aerobim.core.di.container import Container
from aerobim.core.di.tokens import Tokens

if TYPE_CHECKING:
    from fastapi import FastAPI


def create_http_app(container: Container) -> FastAPI:
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install FastAPI and Pydantic to run the HTTP API") from exc

    # Imported lazily: these modules import FastAPI at module level, and the
    # guard above must stay the single failure point when it is missing.
    from aerobim.presentation.http.context import ApiContext
    from aerobim.presentation.http.correlation import add_correlation_middleware
    from aerobim.presentation.http.rate_limit import (
        _DEFAULT_JOB_POLL_PER_MINUTE,
        add_rate_limit_middleware,
    )
    from aerobim.presentation.http.routes.analyze import build_analyze_router
    from aerobim.presentation.http.routes.exports import build_exports_router
    from aerobim.presentation.http.routes.norm_packs import build_norm_packs_router
    from aerobim.presentation.http.routes.reports import build_reports_router
    from aerobim.presentation.http.routes.system import build_system_router
    from aerobim.presentation.http.routes.uploads import build_uploads_router
    from aerobim.presentation.http.security_headers import (
        add_auth_header_hygiene_middleware,
        add_security_headers_middleware,
    )

    settings = container.resolve(Tokens.SETTINGS)

    # Harden OpenAPI surfaces outside development/test (RT A03).
    if not settings.is_dev_environment:
        app = FastAPI(
            title="aerobim-backend",
            version="0.2.0",
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
        )
    else:
        app = FastAPI(title="aerobim-backend", version="0.2.0")

    # Innermost first. Last add_middleware is outermost (Starlette).
    # Rate-limit must sit inside security-headers/correlation so 429 keeps CSP/HSTS
    # and X-Request-ID (HD-MW-01). CORS stays outside rate-limit so OPTIONS preflight
    # is not 429'd before the CORS response.
    job_poll_per_minute = (
        _DEFAULT_JOB_POLL_PER_MINUTE
        if settings.signoff_profile in {"samolet_pilot", "production"}
        else 0
    )
    cors_origins = list(settings.cors_origins)
    # credentials:include on the review shell needs Allow-Credentials; Starlette
    # forbids that together with origin "*". Empty origins stay credential-less.
    # Hard profiles default credentials off unless from_env opted in (F-11).
    cors_credentials = (
        bool(cors_origins) and "*" not in cors_origins and bool(settings.cors_allow_credentials)
    )
    add_rate_limit_middleware(
        app,
        requests_per_minute=settings.http_rate_limit_per_minute,
        job_poll_per_minute=job_poll_per_minute,
        redis_url=settings.redis_url,
        signoff_profile=settings.signoff_profile,
        fail_closed=not settings.is_dev_environment,
        trusted_proxy_ips=settings.http_trusted_proxy_ips,
    )
    add_auth_header_hygiene_middleware(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_credentials,
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-Request-ID",
            "Accept",
        ],
        expose_headers=["X-Request-ID"],
    )
    add_correlation_middleware(app)
    add_security_headers_middleware(app)

    ctx = ApiContext(container)

    # Inclusion order mirrors the historical registration order in this module.
    app.include_router(build_system_router(ctx))
    if settings.is_dev_environment:
        from aerobim.presentation.http.routes.demo import build_demo_router

        app.include_router(build_demo_router(ctx))
    app.include_router(build_uploads_router(ctx))
    app.include_router(build_analyze_router(ctx))
    app.include_router(build_reports_router(ctx))
    app.include_router(build_norm_packs_router(ctx))
    app.include_router(build_exports_router(ctx))

    return app


def _esc(value: str) -> str:
    """HTML-escape user-controlled values for element text and attributes."""
    from aerobim.presentation.http.report_html import _esc as esc

    return esc(value)
