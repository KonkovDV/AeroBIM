"""Canonical content hashing for norm rule packs (sign-off integrity)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
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


def compute_directory_tree_hash(root: Path) -> str:
    """SHA-256 of sorted relative paths + file digests. Not a customer pack_hash.

    Text files are hashed as LF (Linux CI), matching samples manifest gating.
    """

    if not root.is_dir():
        raise FileNotFoundError(f"directory not found: {root}")
    lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if b"\r\n" in data and b"\x00" not in data[:8192]:
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                pass
            else:
                data = data.replace(b"\r\n", b"\n")
        digest = hashlib.sha256(data).hexdigest()
        lines.append(f"{rel} {digest}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
