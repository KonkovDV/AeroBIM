"""System surface routes: health probe, auth BFF discovery, capability honesty."""

from typing import Annotated

from fastapi import APIRouter, Depends

from aerobim.domain.object_acl import AuthPrincipal
from aerobim.domain.system_capabilities import (
    build_auth_bff_capability,
    build_system_capabilities_payload,
)
from aerobim.presentation.http.context import ApiContext


def build_system_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, object]:
        # Do not disclose AEROBIM_ENV on the unauthenticated probe surface.
        return {
            "service": ctx.settings.application_name,
            "status": "ok",
        }

    @router.get("/v1/auth/bff")
    def get_auth_bff_status():
        """Public discovery: POST-05 OIDC BFF is designed but not implemented."""

        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=501, content=build_auth_bff_capability())

    @router.get("/v1/system/capabilities")
    def get_system_capabilities(
        principal: Annotated[AuthPrincipal, Depends(ctx.require_bearer_auth)],
    ) -> dict[str, object]:
        """Static honesty surface for DWG/CV/MEP/calculation claim boundaries."""

        return build_system_capabilities_payload()

    return router
