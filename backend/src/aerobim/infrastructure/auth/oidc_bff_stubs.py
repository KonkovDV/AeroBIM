"""POST-05 OIDC BFF Phase 2 stubs — CSRF state store, no production IdP or session cookie.

Honesty: ``auth_bff.status`` stays ``NOT_IMPLEMENTED`` until Phase 3 ships a verified
HttpOnly session cookie path. These routes exist for contract testing and CSRF binding
only — callback must not issue production SSO session cookies.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

from aerobim.domain.system_capabilities import build_auth_bff_capability

_STATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class OidcBffStubState:
    """One-time CSRF ``state`` issued by ``/v1/auth/login``."""

    state: str
    created_at: float
    redirect_uri: str | None = None


class InMemoryOidcBffStateStore:
    """Process-local CSRF state store (Phase 2 stub — not production session storage)."""

    def __init__(self, *, ttl_seconds: int = _STATE_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._states: dict[str, OidcBffStubState] = {}

    def issue(self, *, redirect_uri: str | None = None) -> OidcBffStubState:
        self._purge_expired()
        state = secrets.token_urlsafe(32)
        entry = OidcBffStubState(
            state=state,
            created_at=time.monotonic(),
            redirect_uri=redirect_uri,
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


def build_login_stub_payload(
    *,
    state_entry: OidcBffStubState,
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    """Honesty stub login response — no IdP redirect, no session cookie."""

    capability = build_auth_bff_capability()
    return {
        **capability,
        "phase": 2,
        "stub": True,
        "state": state_entry.state,
        "redirect_uri": redirect_uri or state_entry.redirect_uri,
        "idp_redirect_url": None,
        "message": (
            "Phase 2 stub: CSRF state issued; no production IdP or session cookie. "
            "auth_bff remains NOT_IMPLEMENTED until Phase 3."
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
    "build_login_stub_payload",
    "build_logout_stub_payload",
]
