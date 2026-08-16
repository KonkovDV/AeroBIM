"""Privacy Guard: minimize + pseudonymize before external egress (brief §8, P1).

Domain-pure. Masking **reduces disclosure; it does NOT prove anonymity** — structure,
geometry, rare values and system names can re-identify. Honest guarantees:

- Pseudonyms are deterministic PER TENANT (so the deterministic engine can still join
  the same entity) and **unlinkable ACROSS tenants** (one shared deployment salt with
  a tenant-bound, length-prefixed HMAC input): the same raw value yields different
  tokens for different tenants.
- Tokens are opaque ``sha256`` prefixes — a model cannot reverse a token, and the
  salt / restore key is never part of any payload.
- The restore table (``TokenVault``) is **local-only and tenant-scoped**: a restore
  for the wrong tenant returns ``None``. It never leaves the local contour. Per-tenant
  LRU cap (default 4096) evicts oldest mappings; restore of an evicted token is
  ``None`` (HD4-PG-03).
- Fail-closed field policy: a field not explicitly ``keep``/``tokenize`` is REMOVED
  (do not egress fields the policy did not allow).
- Restore must run ONLY after response verification and must never feed the verdict
  without a deterministic check (enforced by the caller / verdict layer, not here).
- A blank tenant is refused (cannot scope isolation) — fail closed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_MASK_VERSION = "1.0.0"
# HD4-PG-02: substring scan skips needles shorter than this (JSON punctuation /
# trivial tokens such as "A1"). Short secrets are a documented residual.
_MIN_LEAK_SCAN_CHARS = 3
# HD4-PG-03: per-tenant restore-table cap (process-lifetime; eviction is LRU).
_DEFAULT_VAULT_CAP = 4096


class PrivacyLeakError(ValueError):
    """Raised when a masked payload would still carry a sensitive raw value."""


def _canonical_component(value: str, label: str) -> str:
    """Trim + reject control chars (kills \\x1f delimiter-collision in hash material)."""
    text = str(value).strip()
    if any(ord(ch) < 0x20 for ch in text):
        raise ValueError(f"{label} must not contain control characters")
    return text


def _canonical_tenant(tenant_id: str) -> str:
    text = _canonical_component(tenant_id or "", "tenant_id")
    if not text:
        raise ValueError("tenant_id is required (fail-closed)")
    return text


def _residual_needles(value: Any) -> tuple[str, ...]:
    """Python ``str`` and JSON atom forms (HD4-PG-02: ``True`` vs ``true``)."""
    python_form = str(value)
    try:
        json_form = json.dumps(value, ensure_ascii=False)
    except TypeError:
        json_form = json.dumps(python_form, ensure_ascii=False)
    needles: list[str] = []
    for candidate in (python_form, json_form):
        if len(candidate) >= _MIN_LEAK_SCAN_CHARS and candidate not in needles:
            needles.append(candidate)
    return tuple(needles)


def _assert_no_residual_leak(masked: Mapping[str, Any], sensitive_values: list[Any]) -> None:
    """Fail closed if a kept field still contains a tokenized/removed raw value.

    Needles shorter than ``_MIN_LEAK_SCAN_CHARS`` are skipped (documented residual).
    """
    serialized = json.dumps(masked, ensure_ascii=False, default=str)
    for raw in sensitive_values:
        for needle in _residual_needles(raw):
            if needle in serialized:
                raise PrivacyLeakError("masked output still contains a sensitive raw value")


@dataclass(frozen=True)
class MaskResult:
    """Outcome of masking a payload for egress (records what left and what was cut)."""

    masked: dict[str, Any]
    fields_sent: tuple[str, ...]
    fields_removed: tuple[str, ...]
    fields_tokenized: tuple[str, ...]
    mask_version: str = _MASK_VERSION


class TokenVault:
    """Local-only, tenant-scoped restore table. Never serialized or egressed.

    HD4-PG-03: bounded per tenant (LRU). Restore of an evicted token returns
    ``None`` — masking is not a durable identity store.
    """

    def __init__(self, *, max_entries_per_tenant: int = _DEFAULT_VAULT_CAP) -> None:
        if max_entries_per_tenant < 1:
            raise ValueError("max_entries_per_tenant must be >= 1")
        self._max_entries_per_tenant = max_entries_per_tenant
        self._by_tenant: dict[str, OrderedDict[str, str]] = {}
        self.evictions = 0

    def put(self, *, tenant_id: str, token: str, original: str) -> None:
        bucket = self._by_tenant.setdefault(tenant_id, OrderedDict())
        existing = bucket.get(token)
        if existing is not None and existing != original:
            # A truncated-digest collision would silently corrupt restore — fail closed.
            raise ValueError(f"token collision for tenant {tenant_id!r}: {token}")
        bucket[token] = original
        bucket.move_to_end(token)
        while len(bucket) > self._max_entries_per_tenant:
            bucket.popitem(last=False)
            self.evictions += 1

    def restore(self, *, tenant_id: str, token: str) -> str | None:
        bucket = self._by_tenant.get(tenant_id)
        if bucket is None:
            return None
        return bucket.get(token)


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
        tenant = _canonical_tenant(tenant_id)
        safe_kind = _canonical_component(kind or "value", "kind").lower() or "value"
        digest = self._pseudonym_digest(tenant, safe_kind, str(value))
        token = f"TKN_{safe_kind.upper()}_{digest}"
        self._vault.put(tenant_id=tenant, token=token, original=str(value))
        return token

    def _pseudonym_digest(self, tenant: str, kind: str, value: str) -> str:
        """Length-prefixed HMAC(salt) over (tenant, kind, value) — no delimiter shift.

        HMAC keeps the salt out of the hash pre-image; length-prefixing each part
        removes the boundary collision where two different (tenant, kind) splits hash
        the same. 128-bit (32-hex) output keeps the token opaque while making a
        truncation collision astronomically unlikely.
        """
        mac = hmac.new(self._salt.encode("utf-8"), digestmod=hashlib.sha256)
        for part in (tenant, kind, value):
            encoded = part.encode("utf-8")
            mac.update(len(encoded).to_bytes(8, "big"))
            mac.update(encoded)
        return mac.hexdigest()[:32]

    def restore(self, token: str, *, tenant_id: str) -> str | None:
        """Local, tenant-scoped reverse lookup (wrong/blank tenant → None)."""
        text = str(tenant_id or "").strip()
        if not text or any(ord(ch) < 0x20 for ch in text):
            return None
        return self._vault.restore(tenant_id=text, token=token)

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
        tenant = _canonical_tenant(tenant_id)
        masked: dict[str, Any] = {}
        sent: list[str] = []
        removed: list[str] = []
        tokenized: list[str] = []
        sensitive_values: list[Any] = []
        for key, value in payload.items():
            action = rules.get(key, "remove")  # fail-closed default: drop unlisted
            if action == "keep":
                if isinstance(value, (dict, list, tuple, set)):
                    # Nested containers can smuggle unlisted sensitive fields — fail closed.
                    raise ValueError(f"'keep' on non-scalar field {key!r} is not allowed")
                masked[key] = value
                sent.append(key)
            elif action.startswith("tokenize:"):
                kind = action.split(":", 1)[1] or key
                sensitive_values.append(value)
                masked[key] = self.tokenize(str(value), tenant_id=tenant, kind=kind)
                sent.append(key)
                tokenized.append(key)
            else:
                sensitive_values.append(value)
                removed.append(key)
        _assert_no_residual_leak(masked, sensitive_values)
        return MaskResult(
            masked=masked,
            fields_sent=tuple(sent),
            fields_removed=tuple(removed),
            fields_tokenized=tuple(tokenized),
        )


__all__ = [
    "MaskResult",
    "PrivacyGuard",
    "PrivacyLeakError",
    "TokenVault",
    "truncate_flagged",
]
