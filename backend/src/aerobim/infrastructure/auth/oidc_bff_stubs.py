"""POST-05 OIDC BFF Phase 2/2.5 stubs — CSRF + PKCE S256, no production session.

Honesty: ``auth_bff.status`` stays ``NOT_IMPLEMENTED`` until a production IdP
path is evidenced. Phase 2.5 adds PKCE material and an optional IdP authorize URL
*draft* when lab env is set — still HTTP 501 by default, never a production SSO.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from aerobim.domain.system_capabilities import build_auth_bff_capability

_STATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class OidcBffStubState:
    """One-time CSRF ``state`` (+ PKCE verifier + OIDC nonce, server-side)."""

    state: str
    created_at: float
    redirect_uri: str | None = None
    code_verifier: str | None = None
    code_challenge: str | None = None
    nonce: str | None = None


class InMemoryOidcBffStateStore:
    """Process-local CSRF+PKCE state store (Phase 2 stub — not production session storage)."""

    def __init__(self, *, ttl_seconds: int = _STATE_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._states: dict[str, OidcBffStubState] = {}

    def issue(self, *, redirect_uri: str | None = None) -> OidcBffStubState:
        self._purge_expired()
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        nonce = secrets.token_urlsafe(32)
        entry = OidcBffStubState(
            state=state,
            created_at=time.monotonic(),
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            nonce=nonce,
        )
        self._states[state] = entry
        return entry

    def consume(self, state: str) -> OidcBffStubState | None:
        """Validate and remove a one-time state (CSRF binding)."""

        self._purge_expired()
        entry = self._states.pop(state, None)
        if entry is None:
            return None
        if time.monotonic() - entry.created_at > self._ttl_seconds:
            return None
        return entry

    def clear(self) -> None:
        self._states.clear()

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key for key, entry in self._states.items() if now - entry.created_at > self._ttl_seconds
        ]
        for key in expired:
            del self._states[key]


# Module-level store for the stub BFF (Phase 2 — in-memory only).
DEFAULT_BFF_STATE_STORE = InMemoryOidcBffStateStore()


def build_idp_authorize_url_draft(
    *,
    authorize_endpoint: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    nonce: str,
    scope: str = "openid profile",
) -> str:
    """Build Authorization Code + PKCE authorize URL (lab draft only).

    Callers must not treat presence of this URL as production BFF readiness.
    ``nonce`` is required (OpenID Connect Core) so an ``id_token`` can be bound
    to this login attempt.
    """

    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    base = authorize_endpoint.rstrip("?")
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}{query}"


def build_login_stub_payload(
    *,
    state_entry: OidcBffStubState,
    redirect_uri: str | None = None,
    authorize_endpoint: str | None = None,
    client_id: str | None = None,
    redirect_uri_allowlist: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Honesty stub login — CSRF+PKCE issued; optional IdP URL draft; no session cookie."""

    capability = build_auth_bff_capability()
    effective_redirect = redirect_uri or state_entry.redirect_uri
    idp_redirect_url: str | None = None
    allow = tuple(redirect_uri_allowlist or ())
    redirect_allowed = bool(effective_redirect) and effective_redirect in allow
    if (
        authorize_endpoint
        and client_id
        and redirect_allowed
        and state_entry.code_challenge
        and state_entry.nonce
    ):
        idp_redirect_url = build_idp_authorize_url_draft(
            authorize_endpoint=authorize_endpoint,
            client_id=client_id,
            redirect_uri=effective_redirect,  # type: ignore[arg-type]
            state=state_entry.state,
            code_challenge=state_entry.code_challenge,
            nonce=state_entry.nonce,
        )
    return {
        **capability,
        "phase": 2,
        "stub": True,
        "state": state_entry.state,
        "redirect_uri": effective_redirect,
        "pkce": {
            "code_challenge_method": "S256",
            "code_challenge": state_entry.code_challenge,
            # code_verifier stays server-side only
        },
        "idp_redirect_url": idp_redirect_url,
        "redirect_uri_allowlisted": redirect_allowed,
        "message": (
            "Phase 2.5 stub: CSRF state + PKCE S256 issued; IdP authorize URL draft "
            "only when AEROBIM_OIDC_BFF_* lab env is set AND redirect_uri is "
            "allowlisted. No production session cookie. auth_bff remains "
            "NOT_IMPLEMENTED until Phase 3."
        ),
    }


def build_callback_stub_payload(*, state: str, code: str | None = None) -> dict[str, Any]:
    """Honesty stub callback — acknowledges state binding without SSO session."""

    capability = build_auth_bff_capability()
    return {
        **capability,
        "phase": 2,
        "stub": True,
        "state": state,
        "code_received": bool(code),
        "session_cookie_issued": False,
        "message": (
            "Phase 2 stub: callback received; no production session cookie issued. "
            "auth_bff remains NOT_IMPLEMENTED until Phase 3."
        ),
    }


def build_logout_stub_payload() -> dict[str, Any]:
    """Honesty stub logout — no session revoke; does not wipe global CSRF store."""

    capability = build_auth_bff_capability()
    return {
        **capability,
        "phase": 2,
        "stub": True,
        "session_cookie_cleared": False,
        "csrf_store_cleared": False,
        "message": (
            "Phase 2 stub: logout honesty only — no production session and no global "
            "CSRF store wipe (avoids anonymous DoS). auth_bff remains NOT_IMPLEMENTED."
        ),
    }


__all__ = [
    "DEFAULT_BFF_STATE_STORE",
    "InMemoryOidcBffStateStore",
    "OidcBffStubState",
    "build_callback_stub_payload",
    "build_idp_authorize_url_draft",
    "build_login_stub_payload",
    "build_logout_stub_payload",
]
