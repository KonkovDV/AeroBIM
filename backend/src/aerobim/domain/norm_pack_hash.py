"""Canonical content hashing for norm rule packs (sign-off integrity)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_norm_pack_content_hash(payload: dict[str, Any]) -> str:
    """Canonical SHA-256 over pack identity + rules (excludes mutable hash fields)."""

    canonical = {
        "pack_id": payload.get("pack_id"),
        "version": payload.get("version"),
        "jurisdiction": payload.get("jurisdiction"),
        "status": payload.get("status"),
        "rules": payload.get("rules"),
    }
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
