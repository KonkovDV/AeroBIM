"""Privacy Guard: minimize + pseudonymize before external egress (brief §8, P1).

Domain-pure. Masking **reduces disclosure; it does NOT prove anonymity** — structure,
geometry, rare values and system names can re-identify. Honest guarantees:

- Pseudonyms are deterministic PER TENANT (so the deterministic engine can still join
  the same entity) and **unlinkable ACROSS tenants** (per-tenant salt): the same raw
  value yields different tokens for different tenants.
- Tokens are opaque ``sha256`` prefixes — a model cannot reverse a token, and the
  salt / restore key is never part of any payload.
- The restore table (``TokenVault``) is **local-only and tenant-scoped**: a restore
  for the wrong tenant returns ``None``. It never leaves the local contour.
- Fail-closed field policy: a field not explicitly ``keep``/``tokenize`` is REMOVED
  (do not egress fields the policy did not allow).
- Restore must run ONLY after response verification and must never feed the verdict
  without a deterministic check (enforced by the caller / verdict layer, not here).
- A blank tenant is refused (cannot scope isolation) — fail closed.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_MASK_VERSION = "1.0.0"
_UNIT_SEP = "\x1f"


@dataclass(frozen=True)
class MaskResult:
    """Outcome of masking a payload for egress (records what left and what was cut)."""

    masked: dict[str, Any]
    fields_sent: tuple[str, ...]
    fields_removed: tuple[str, ...]
    fields_tokenized: tuple[str, ...]
    mask_version: str = _MASK_VERSION


class TokenVault:
    """Local-only, tenant-scoped restore table. Never serialized or egressed."""

    def __init__(self) -> None:
        self._by_tenant: dict[str, dict[str, str]] = {}

    def put(self, *, tenant_id: str, token: str, original: str) -> None:
        self._by_tenant.setdefault(tenant_id, {})[token] = original

    def restore(self, *, tenant_id: str, token: str) -> str | None:
        return self._by_tenant.get(tenant_id, {}).get(token)


def truncate_flagged(value: str, *, max_len: int) -> tuple[str, bool]:
    """Bounded text + a flag, so a truncated (corrupted) display is never silent."""
    if max_len < 0:
        raise ValueError("max_len must be non-negative")
    if len(value) <= max_len:
        return value, False
    return value[:max_len], True


class PrivacyGuard:
    """Deterministic per-tenant pseudonymizer + fail-closed field masker."""

    def __init__(self, *, tenant_salt: str, vault: TokenVault | None = None) -> None:
        if not tenant_salt or not tenant_salt.strip():
            raise ValueError("tenant_salt is required (local secret; never egressed)")
        self._salt = tenant_salt
        self._vault = vault if vault is not None else TokenVault()

    def tokenize(self, value: str, *, tenant_id: str, kind: str) -> str:
        """Opaque, deterministic-per-tenant token; stores the reverse map locally."""
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required to tokenize (fail-closed)")
        safe_kind = (kind or "value").strip().lower() or "value"
        material = _UNIT_SEP.join((self._salt, tenant_id, safe_kind, str(value)))
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
        token = f"TKN_{safe_kind.upper()}_{digest}"
        self._vault.put(tenant_id=tenant_id, token=token, original=str(value))
        return token

    def restore(self, token: str, *, tenant_id: str) -> str | None:
        """Local, tenant-scoped reverse lookup (wrong tenant → None)."""
        if not tenant_id or not tenant_id.strip():
            return None
        return self._vault.restore(tenant_id=tenant_id, token=token)

    def mask_payload(
        self,
        payload: Mapping[str, Any],
        *,
        tenant_id: str,
        rules: Mapping[str, str],
    ) -> MaskResult:
        """Apply per-field rules; fields not listed as keep/tokenize are REMOVED.

        ``rules[field]`` ∈ ``"keep"`` | ``"remove"`` | ``"tokenize:<kind>"``.
        """
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required to mask (fail-closed)")
        masked: dict[str, Any] = {}
        sent: list[str] = []
        removed: list[str] = []
        tokenized: list[str] = []
        for key, value in payload.items():
            action = rules.get(key, "remove")  # fail-closed default: drop unlisted
            if action == "keep":
                masked[key] = value
                sent.append(key)
            elif action.startswith("tokenize:"):
                kind = action.split(":", 1)[1] or key
                masked[key] = self.tokenize(str(value), tenant_id=tenant_id, kind=kind)
                sent.append(key)
                tokenized.append(key)
            else:
                removed.append(key)
        return MaskResult(
            masked=masked,
            fields_sent=tuple(sent),
            fields_removed=tuple(removed),
            fields_tokenized=tuple(tokenized),
        )


__all__ = [
    "MaskResult",
    "PrivacyGuard",
    "TokenVault",
    "truncate_flagged",
]
