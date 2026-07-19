"""OIDC JWT access-token validation (RS256, iss/aud/exp) for enterprise SSO.

Follows 2026 FastAPI/OIDC practice: pin algorithms, validate issuer + audience +
expiry, fetch JWKS from the IdP. Static API bearer remains supported in parallel.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any


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

    def validate(self, token: str) -> dict[str, Any]:
        try:
            import jwt
            from jwt import PyJWKClient
        except ModuleNotFoundError as exc:
            raise OidcValidationError(
                "OIDC JWT validation requires PyJWT; install the 'enterprise' extra"
            ) from exc

        jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "require": ["exp", "iss", "aud"],
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                },
            )
        except Exception as exc:  # noqa: BLE001 — normalize library errors
            raise OidcValidationError(f"OIDC token validation failed: {exc}") from exc

        if not isinstance(claims, dict):
            raise OidcValidationError("OIDC token claims must be an object")
        return claims

    def fetch_jwks(self) -> dict[str, Any]:
        """Optional diagnostic helper; PyJWKClient handles runtime JWKS fetch."""
        now = time.time()
        if (
            self._jwks_cache is not None
            and now - self._jwks_fetched_at < self.jwks_cache_ttl_seconds
        ):
            return self._jwks_cache
        from aerobim.core.security.outbound_url import assert_safe_outbound_url, safe_urlopen

        assert_safe_outbound_url(self.jwks_url, allow_http=False, resolve_dns=True)
        req = urllib.request.Request(self.jwks_url, method="GET")
        with safe_urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise OidcValidationError("JWKS response must be a JSON object")
        self._jwks_cache = payload
        self._jwks_fetched_at = now
        return payload
