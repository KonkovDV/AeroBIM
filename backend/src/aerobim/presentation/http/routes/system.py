"""System surface routes: health probe, auth BFF discovery, capability honesty."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from aerobim.domain.object_acl import AuthPrincipal
from aerobim.domain.system_capabilities import (
    build_auth_bff_capability,
    build_system_capabilities_payload,
)
from aerobim.infrastructure.auth.oidc_bff_stubs import (
    DEFAULT_BFF_STATE_STORE,
    build_callback_stub_payload,
    build_login_stub_payload,
    build_logout_stub_payload,
)
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.schemas import SystemCapabilitiesResponse


def build_system_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    bff_store = DEFAULT_BFF_STATE_STORE

    @router.get("/health")
    def health() -> dict[str, object]:
        # Do not disclose AEROBIM_ENV on the unauthenticated probe surface.
        return {
            "service": ctx.settings.application_name,
            "status": "ok",
        }

    @router.get("/v1/auth/bff")
    def get_auth_bff_status() -> JSONResponse:
        """Public discovery: POST-05 OIDC BFF is designed but not implemented."""

        return JSONResponse(status_code=501, content=build_auth_bff_capability())

    @router.get("/v1/auth/login")
    def auth_login_stub(
        redirect_uri: Annotated[str | None, Query()] = None,
    ) -> JSONResponse:
        """Phase 2 stub: issue CSRF state; no production IdP redirect or session cookie."""

        state_entry = bff_store.issue(redirect_uri=redirect_uri)
        return JSONResponse(
            status_code=501,
            content=build_login_stub_payload(
                state_entry=state_entry,
                redirect_uri=redirect_uri,
            ),
        )

    @router.get("/v1/auth/callback")
    def auth_callback_stub(
        state: Annotated[str | None, Query()] = None,
        code: Annotated[str | None, Query()] = None,
    ) -> JSONResponse:
        """Phase 2 stub: validate CSRF state; never issue production SSO session cookie."""

        if not state or bff_store.consume(state) is None:
            return JSONResponse(
                status_code=400,
                content={
                    **build_auth_bff_capability(),
                    "phase": 2,
                    "stub": True,
                    "error": "invalid_or_missing_csrf_state",
                    "message": "CSRF state rejected — no session cookie issued.",
                },
            )
        return JSONResponse(
            status_code=501,
            content=build_callback_stub_payload(state=state, code=code),
        )

    @router.post("/v1/auth/logout")
    def auth_logout_stub() -> JSONResponse:
        """Phase 2 stub: honesty only — does not clear global CSRF state or sessions.

        Public logout must not wipe process-wide CSRF ``state`` (anonymous DoS).
        Phase 3 will bind logout to a verified session cookie.
        """

        return JSONResponse(status_code=501, content=build_logout_stub_payload())

    @router.get("/v1/system/capabilities", response_model=SystemCapabilitiesResponse)
    def get_system_capabilities(
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> SystemCapabilitiesResponse:
        """Static honesty surface for DWG/CV/MEP/calculation claim boundaries.

        Response contract is pinned field-by-field (schema_version 1.3.0):
        model validation here means a payload drift fails loudly instead of
        silently loosening the published OpenAPI document.
        """

        return SystemCapabilitiesResponse.model_validate(build_system_capabilities_payload())

    return router
