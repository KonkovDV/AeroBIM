"""System surface routes: health probe, auth BFF discovery, capability honesty."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from aerobim.domain.object_acl import AuthPrincipal
from aerobim.domain.system_capabilities import (
    build_auth_bff_capability,
    build_system_capabilities_payload,
)
from aerobim.infrastructure.auth.oidc_bff_phase3 import (
    DEFAULT_BFF_SESSION_STORE,
    OidcBffSession,
    build_phase3_login_payload,
    build_phase3_session_payload,
    exchange_authorization_code,
    parse_session_cookie,
    session_cookie_name,
    session_from_token_payload,
    sign_session_cookie,
)
from aerobim.infrastructure.auth.oidc_bff_stubs import (
    DEFAULT_BFF_STATE_STORE,
    build_callback_stub_payload,
    build_login_stub_payload,
    build_logout_stub_payload,
)
from aerobim.infrastructure.security.oidc_token_validator import OidcValidationError
from aerobim.presentation.http.context import ApiContext
from aerobim.presentation.http.schemas import SystemCapabilitiesResponse


def build_system_router(ctx: ApiContext) -> APIRouter:
    router = APIRouter()
    bff_store = DEFAULT_BFF_STATE_STORE
    session_store = DEFAULT_BFF_SESSION_STORE

    def _cookie_secure() -> bool:
        return not ctx.settings.debug and not ctx.settings.is_dev_environment

    def _cookie_secret() -> str:
        return ctx.settings.oidc_bff_cookie_secret or ""

    def _cookie_name() -> str:
        return session_cookie_name(secure=_cookie_secure())

    def _session_from_request(request: Request) -> OidcBffSession | None:
        raw = request.cookies.get(_cookie_name())
        session_id = parse_session_cookie(raw, _cookie_secret())
        if session_id is None:
            return None
        return session_store.get(session_id)

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

        payload = build_auth_bff_capability()
        if ctx.settings.oidc_bff_phase3_ready:
            payload = {**payload, "status": "LAB", "phase": 3}
            return JSONResponse(status_code=200, content=payload)
        return JSONResponse(status_code=501, content=payload)

    @router.get("/v1/auth/login")
    def auth_login(
        redirect_uri: Annotated[str | None, Query()] = None,
    ) -> JSONResponse:
        """Phase 2.5 stub or Phase 3 lab login (IdP authorize URL)."""

        state_entry = bff_store.issue(redirect_uri=redirect_uri)
        stub = build_login_stub_payload(
            state_entry=state_entry,
            redirect_uri=redirect_uri,
            authorize_endpoint=ctx.settings.oidc_bff_authorize_url,
            client_id=ctx.settings.oidc_bff_client_id,
            redirect_uri_allowlist=ctx.settings.oidc_bff_redirect_uri_allowlist,
        )
        if not ctx.settings.oidc_bff_phase3_ready:
            return JSONResponse(status_code=501, content=stub)
        payload = build_phase3_login_payload(
            state_entry=state_entry,
            idp_redirect_url=stub.get("idp_redirect_url")
            if isinstance(stub.get("idp_redirect_url"), str)
            else None,
            redirect_uri=redirect_uri,
        )
        return JSONResponse(status_code=200, content={**build_auth_bff_capability(), **payload})

    @router.get("/v1/auth/callback")
    def auth_callback(
        state: Annotated[str | None, Query()] = None,
        code: Annotated[str | None, Query()] = None,
    ) -> JSONResponse:
        """Phase 2 stub or Phase 3 code exchange + HttpOnly session cookie."""

        consumed = bff_store.consume(state) if state else None
        if not state or consumed is None:
            return JSONResponse(
                status_code=400,
                content={
                    **build_auth_bff_capability(),
                    "phase": 3 if ctx.settings.oidc_bff_phase3_ready else 2,
                    "stub": not ctx.settings.oidc_bff_phase3_ready,
                    "error": "invalid_or_missing_csrf_state",
                    "message": "CSRF state rejected — no session cookie issued.",
                },
            )
        if not ctx.settings.oidc_bff_phase3_ready:
            return JSONResponse(
                status_code=501,
                content=build_callback_stub_payload(state=state, code=code),
            )
        if not code:
            return JSONResponse(
                status_code=400,
                content={
                    **build_auth_bff_capability(),
                    "phase": 3,
                    "stub": False,
                    "error": "missing_authorization_code",
                    "message": "Phase 3 callback requires an authorization code.",
                },
            )
        redirect_uri = consumed.redirect_uri or ""
        if redirect_uri not in ctx.settings.oidc_bff_redirect_uri_allowlist:
            return JSONResponse(
                status_code=400,
                content={
                    **build_auth_bff_capability(),
                    "phase": 3,
                    "stub": False,
                    "error": "invalid_redirect_uri",
                    "message": "Callback redirect_uri is not on the BFF allowlist.",
                },
            )
        try:
            tokens = exchange_authorization_code(
                token_url=ctx.settings.oidc_bff_token_url or "",
                client_id=ctx.settings.oidc_bff_client_id or "",
                client_secret=ctx.settings.oidc_bff_client_secret or "",
                code=code,
                redirect_uri=redirect_uri,
                code_verifier=consumed.code_verifier,
            )
            subject, email, identity_verified = session_from_token_payload(
                tokens,
                validator=ctx.oidc_validator,
                expected_nonce=consumed.nonce,
            )
        except OidcValidationError as exc:
            return JSONResponse(
                status_code=502,
                content={
                    **build_auth_bff_capability(),
                    "phase": 3,
                    "stub": False,
                    "error": "identity_verification_failed",
                    "message": str(exc),
                },
            )
        except RuntimeError as exc:
            return JSONResponse(
                status_code=502,
                content={
                    **build_auth_bff_capability(),
                    "phase": 3,
                    "stub": False,
                    "error": "token_exchange_failed",
                    "message": str(exc),
                },
            )
        session = session_store.issue(
            subject=subject,
            access_token=str(tokens.get("access_token") or "") or None,
            id_token=str(tokens.get("id_token") or "") or None,
            email=email,
            identity_verified=identity_verified,
        )
        payload = {
            **build_auth_bff_capability(),
            "status": "LAB",
            "phase": 3,
            "stub": False,
            "session_cookie_issued": True,
            "sub": subject,
            "message": "Phase 3 lab session cookie issued; tokens stay server-side.",
        }
        json_response = JSONResponse(status_code=200, content=payload)
        json_response.set_cookie(
            key=_cookie_name(),
            value=sign_session_cookie(session.session_id, _cookie_secret()),
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
            max_age=3600,
        )
        return json_response

    @router.post("/v1/auth/logout")
    def auth_logout(request: Request) -> JSONResponse:
        """Phase 2 honesty stub, or Phase 3 session revoke bound to the cookie."""

        if not ctx.settings.oidc_bff_phase3_ready:
            return JSONResponse(status_code=501, content=build_logout_stub_payload())
        session = _session_from_request(request)
        if session is not None:
            session_store.revoke(session.session_id)
        payload = {
            **build_auth_bff_capability(),
            "status": "LAB",
            "phase": 3,
            "stub": False,
            "session_cookie_cleared": True,
            "csrf_store_cleared": False,
            "message": "Phase 3 logout cleared the bound session cookie only.",
        }
        json_response = JSONResponse(status_code=200, content=payload)
        json_response.delete_cookie(key=_cookie_name(), path="/")
        return json_response

    @router.get("/v1/auth/session")
    def auth_session(request: Request) -> JSONResponse:
        """Return the current BFF session (Phase 3 lab) without exposing tokens."""

        if not ctx.settings.oidc_bff_phase3_ready:
            return JSONResponse(
                status_code=501,
                content={
                    **build_auth_bff_capability(),
                    "authenticated": False,
                    "message": "Phase 3 session endpoint inactive until oidc_bff_phase3_ready.",
                },
            )
        session = _session_from_request(request)
        if session is None:
            return JSONResponse(status_code=401, content={"authenticated": False, "phase": 3})
        return JSONResponse(status_code=200, content=build_phase3_session_payload(session))

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
