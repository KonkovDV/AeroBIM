"""OIDC JWT access-token validation (RS256, iss/aud/exp) for enterprise SSO.

Follows 2026 FastAPI/OIDC practice: pin algorithms, validate issuer + audience +
expiry, fetch JWKS via SSRF-guarded safe_urlopen (never unguarded PyJWKClient HTTP).
Static API bearer remains supported in parallel.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

# Cap the JWKS response so a compromised/hostile IdP (or a TLS-terminating
# proxy) cannot exhaust memory with an oversized body. Real JWKS docs are KiB.
_MAX_JWKS_BYTES = 1 * 1024 * 1024
_FORCE_JWKS_COOLDOWN_S = 30.0
_UNKNOWN_KID_CAP = 256


class OidcValidationError(ValueError):
    """Raised when a bearer token fails OIDC/JWT validation."""


@dataclass
class OidcTokenValidator:
    issuer: str
    audience: str
    jwks_url: str
    algorithms: tuple[str, ...] = ("RS256",)
    jwks_cache_ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_fetched_at: float = 0.0
        self._jwks_force_at: float = 0.0
        self._unknown_kid_until: dict[str, float] = {}
        self.leeway_seconds: int = 60

    def _select_jwk(self, jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
        keys = jwks.get("keys")
        if not isinstance(keys, list) or not keys:
            raise OidcValidationError("JWKS response contains no keys")
        for candidate in keys:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("kid") != kid:
                continue
            key_use = candidate.get("use")
            if key_use is not None and str(key_use).lower() not in {"sig", ""}:
                continue
            return candidate
        return None

    def validate(self, token: str) -> dict[str, Any]:
        try:
            import jwt
            from jwt import PyJWK
        except ModuleNotFoundError as exc:
            raise OidcValidationError(
                "OIDC JWT validation requires PyJWT; install the 'enterprise' extra"
            ) from exc

        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if kid is None or (isinstance(kid, str) and not kid.strip()):
                raise OidcValidationError("OIDC token header missing required kid")
            kid = str(kid).strip()
            jwks = self.fetch_jwks()
            key_data = self._select_jwk(jwks, kid)
            if key_data is None:
                now = time.monotonic()
                if self._unknown_kid_until.get(kid, 0.0) > now:
                    raise OidcValidationError(f"No JWKS key matched kid={kid!r}")
                if now - self._jwks_force_at >= _FORCE_JWKS_COOLDOWN_S:
                    jwks = self.fetch_jwks(force=True)
                    self._jwks_force_at = now
                    key_data = self._select_jwk(jwks, kid)
            if key_data is None:
                now = time.monotonic()
                self._unknown_kid_until[kid] = now + _FORCE_JWKS_COOLDOWN_S
                if len(self._unknown_kid_until) > _UNKNOWN_KID_CAP:
                    oldest = min(self._unknown_kid_until, key=self._unknown_kid_until.get)
                    self._unknown_kid_until.pop(oldest, None)
                raise OidcValidationError(f"No JWKS key matched kid={kid!r}")
            signing_key = PyJWK.from_dict(key_data)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway_seconds,
                options={
                    "require": ["exp", "iss", "aud"],
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                },
            )
        except OidcValidationError:
            raise
        except Exception as exc:  # noqa: BLE001 — normalize library errors
            raise OidcValidationError(f"OIDC token validation failed: {exc}") from exc

        if not isinstance(claims, dict):
            raise OidcValidationError("OIDC token claims must be an object")
        return claims

    def fetch_jwks(self, *, force: bool = False) -> dict[str, Any]:
        """Fetch JWKS through the shared SSRF outbound guard (resolve DNS at fetch)."""
        now = time.monotonic()
        if (
            not force
            and self._jwks_cache is not None
            and now - self._jwks_fetched_at < self.jwks_cache_ttl_seconds
        ):
            return self._jwks_cache
        from aerobim.core.security.outbound_url import assert_safe_outbound_url, safe_urlopen

        assert_safe_outbound_url(self.jwks_url, allow_http=False, resolve_dns=True)
        req = urllib.request.Request(self.jwks_url, method="GET")
        with safe_urlopen(req, timeout=10) as response:
            # Bounded read: fetch one byte past the cap to detect overflow.
            raw = response.read(_MAX_JWKS_BYTES + 1)
        if len(raw) > _MAX_JWKS_BYTES:
            raise OidcValidationError(f"JWKS response exceeds {_MAX_JWKS_BYTES}-byte cap")
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise OidcValidationError("JWKS response must be a JSON object")
        self._jwks_cache = payload
        self._jwks_fetched_at = now
        return payload
