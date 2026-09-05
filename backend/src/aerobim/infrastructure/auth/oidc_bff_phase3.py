"""POST-05 OIDC BFF Phase 3 — lab-gated session cookie + authorization-code exchange.

Default deployments keep Phase 2 stubs (HTTP 501, auth_bff=NOT_IMPLEMENTED).
Phase 3 activates only when token URL, client secret, cookie secret and
redirect allowlist are all configured **and** the sign-off profile is not
``samolet_pilot`` / ``production``. Public honesty stays NOT_IMPLEMENTED
unless ``Settings.oidc_bff_phase3_ready`` is true (lab / mock IdP).
docker-compose.production.yml is a shared LAN stack, not production SSO.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from aerobim.core.security.object_limits import ObjectTooLargeError, read_http_response_capped
from aerobim.core.security.outbound_url import UnsafeOutboundUrlError, safe_urlopen
from aerobim.domain.auth_roles import extract_oidc_roles
from aerobim.infrastructure.auth.oidc_bff_stubs import OidcBffStubState
from aerobim.infrastructure.security.oidc_token_validator import (
    OidcTokenValidator,
    OidcValidationError,
)

_SESSION_TTL_SECONDS = 3600
SESSION_COOKIE_NAME = "aerobim_bff_session"
HOST_SESSION_COOKIE_NAME = "__Host-aerobim-session"
LAB_AUTHZ_COOKIE_NAME = "aerobim_bff_lab_authz"


@dataclass(frozen=True)
class OidcBffIdentity:
    """Claims extracted from a token-endpoint payload. Not a production SSO claim."""

    subject: str
    email: str | None
    identity_verified: bool
    roles: frozenset[str] = field(default_factory=frozenset)
    tenant_id: str | None = None


@dataclass(frozen=True)
class OidcBffSession:
    session_id: str
    subject: str
    created_at: float
    access_token: str | None = None
    id_token: str | None = None
    email: str | None = None
    identity_verified: bool = False
    roles: frozenset[str] = field(default_factory=frozenset)
    tenant_id: str | None = None


class InMemoryOidcBffSessionStore:
    """Process-local session vault — never returns tokens to JavaScript."""

    def __init__(self, *, ttl_seconds: int = _SESSION_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._sessions: dict[str, OidcBffSession] = {}

    def issue(
        self,
        *,
        subject: str,
        access_token: str | None = None,
        id_token: str | None = None,
        email: str | None = None,
        identity_verified: bool = False,
        roles: frozenset[str] | None = None,
        tenant_id: str | None = None,
    ) -> OidcBffSession:
        self._purge_expired()
        session = OidcBffSession(
            session_id=secrets.token_urlsafe(32),
            subject=subject,
            created_at=time.monotonic(),
            access_token=access_token,
            id_token=id_token,
            email=email,
            identity_verified=identity_verified,
            roles=roles if roles is not None else frozenset(),
            tenant_id=tenant_id,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> OidcBffSession | None:
        self._purge_expired()
        entry = self._sessions.get(session_id)
        if entry is None:
            return None
        if time.monotonic() - entry.created_at > self._ttl_seconds:
            self._sessions.pop(session_id, None)
            return None
        return entry

    def revoke(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def clear(self) -> None:
        self._sessions.clear()

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [
            key
            for key, entry in self._sessions.items()
            if now - entry.created_at > self._ttl_seconds
        ]
        for key in expired:
            del self._sessions[key]


DEFAULT_BFF_SESSION_STORE = InMemoryOidcBffSessionStore()


def session_cookie_name(*, secure: bool) -> str:
    """Prefer __Host- prefix only when Secure cookies are actually used."""

    return HOST_SESSION_COOKIE_NAME if secure else SESSION_COOKIE_NAME


def sign_session_cookie(session_id: str, secret: str) -> str:
    """Bind the opaque session id to ``AEROBIM_OIDC_BFF_COOKIE_SECRET`` (HMAC-SHA256)."""

    digest = hmac.new(
        secret.encode("utf-8"),
        session_id.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{session_id}.{digest}"


def parse_session_cookie(value: str | None, secret: str) -> str | None:
    """Return the session id only when the HMAC matches. Never log ``value``."""

    if not value or not secret or "." not in value:
        return None
    session_id, given = value.rsplit(".", 1)
    if not session_id or not given:
        return None
    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            session_id.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        matched = hmac.compare_digest(expected, given)
    except (UnicodeEncodeError, TypeError, ValueError):
        return None
    if not matched:
        return None
    return session_id


def decode_jwt_payload_unverified(token: str) -> dict[str, Any]:
    """Lab-only JWT payload decode — never proof of identity without a validator."""

    parts = token.split(".")
    if len(parts) < 2:
        return {}
    import base64

    payload = parts[1]
    padded = payload + "=" * (-len(payload) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        data = json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}


def exchange_authorization_code(
    *,
    token_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    code_verifier: str | None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Authorization Code + PKCE token exchange (confidential BFF client)."""

    body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if code_verifier:
        body["code_verifier"] = code_verifier
    encoded = urllib.parse.urlencode(body).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=encoded,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with safe_urlopen(request, timeout=timeout_seconds) as response:
            raw = read_http_response_capped(response)
            payload = json.loads(raw.decode("utf-8"))
    except UnsafeOutboundUrlError as exc:
        raise RuntimeError(f"OIDC token exchange failed SSRF gate: {exc}") from exc
    except ObjectTooLargeError as exc:
        raise RuntimeError("OIDC token exchange failed: response exceeds size cap") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"OIDC token exchange failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("OIDC token endpoint returned a non-object payload")
    return payload


def session_from_token_payload(
    payload: MappingLike,
    *,
    validator: OidcTokenValidator | None = None,
    expected_nonce: str | None = None,
    roles_claim: str = "roles",
    tenant_claim: str = "tenant_id",
) -> OidcBffIdentity:
    """Extract subject + optional email from token-endpoint JSON.

    When ``validator`` is set (issuer/audience/JWKS configured), ``id_token``
    or ``access_token`` is signature-checked. Lab mock IdPs without JWKS keep
    an unverified identity and must surface ``identity_verified=false``.
    ``expected_nonce`` must match the ``id_token`` nonce when an id_token is
    present (OpenID Connect Core).
    """

    id_token = payload.get("id_token")
    access_token = payload.get("access_token")
    if validator is not None:
        token = str(id_token or access_token or "")
        if not token:
            raise OidcValidationError("OIDC session requires a verifiable id_token or access_token")
        claims = validator.validate(token)
        _require_nonce(claims, expected_nonce, require=True)
        subject = str(claims.get("sub") or "unknown")
        email = claims.get("email")
        tenant_raw = claims.get(tenant_claim)
        if isinstance(tenant_raw, str) and tenant_raw.strip():
            tenant_id = tenant_raw.strip()
        else:
            tenant_id = None
        return OidcBffIdentity(
            subject=subject,
            email=str(email) if email else None,
            identity_verified=True,
            roles=extract_oidc_roles(claims, roles_claim=roles_claim),
            tenant_id=tenant_id,
        )
    claims = decode_jwt_payload_unverified(str(id_token)) if id_token else {}
    if id_token:
        _require_nonce(claims, expected_nonce, require=True)
    subject = str(payload.get("sub") or claims.get("sub") or "unknown")
    email = claims.get("email") or payload.get("email")
    email_str = str(email) if email else None
    return OidcBffIdentity(
        subject=subject,
        email=email_str,
        identity_verified=False,
        roles=frozenset(),
        tenant_id=None,
    )


def require_verified_bff_session(session: OidcBffSession | None) -> OidcBffSession:
    """Authz gate: lab sessions with ``identity_verified=False`` must not authorize.

    HTTP API auth may bind a verified BFF cookie to ``AuthPrincipal``. Unverified
    lab sessions still cannot authorize (HD3-BFF-01). Not production SSO.
    """

    if session is None or not session.identity_verified:
        raise PermissionError("unverified OIDC BFF session cannot authorize")
    return session


def _require_nonce(
    claims: MappingLike,
    expected_nonce: str | None,
    *,
    require: bool,
) -> None:
    if not require:
        return
    if not expected_nonce:
        raise OidcValidationError("OIDC login nonce was not bound to CSRF state")
    got = claims.get("nonce")
    if got != expected_nonce:
        raise OidcValidationError("OIDC nonce mismatch")


def build_phase3_login_payload(
    *,
    state_entry: OidcBffStubState,
    idp_redirect_url: str | None,
    redirect_uri: str | None,
) -> dict[str, Any]:
    return {
        "status": "LAB",
        "phase": 3,
        "stub": False,
        "state": state_entry.state,
        "redirect_uri": redirect_uri,
        "idp_redirect_url": idp_redirect_url,
        "session_cookie_issued": False,
        "message": (
            "Phase 3 lab: CSRF+PKCE issued; browser should follow idp_redirect_url. "
            "Public auth_bff remains NOT_IMPLEMENTED unless oidc_bff_phase3_ready."
        ),
    }


def build_phase3_session_payload(session: OidcBffSession) -> dict[str, Any]:
    return {
        "authenticated": True,
        "sub": session.subject,
        "email": session.email,
        "session_id": session.session_id,
        "access_token": None,
        "id_token": None,
        "identity_verified": session.identity_verified,
        "roles": sorted(session.roles),
        "tenant_id": session.tenant_id,
        "phase": 3,
        "production_sso": False,
    }


MappingLike = dict[str, Any]


__all__ = [
    "DEFAULT_BFF_SESSION_STORE",
    "HOST_SESSION_COOKIE_NAME",
    "InMemoryOidcBffSessionStore",
    "LAB_AUTHZ_COOKIE_NAME",
    "OidcBffIdentity",
    "OidcBffSession",
    "SESSION_COOKIE_NAME",
    "build_phase3_login_payload",
    "build_phase3_session_payload",
    "decode_jwt_payload_unverified",
    "exchange_authorization_code",
    "require_verified_bff_session",
    "parse_session_cookie",
    "session_cookie_name",
    "session_from_token_payload",
    "sign_session_cookie",
]
