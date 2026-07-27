"""Deterministic VLM response cache for act-grade replay (§2.1, domain-pure).

The kimi-k3 API fixes sampling and does not document determinism, so it cannot
be relied on for the МИК act. Reproducibility is instead guaranteed by caching
the structured response keyed by ``sha256(image) + sha256(prompt) + model
snapshot``: the first live read populates the cache; every replay returns the
byte-identical stored content, integrity-checked against a golden content hash.

This module is pure (hashing + a store protocol); the filesystem store and the
reader wrapper live in infrastructure.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Protocol


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_sha256(content: dict[str, Any]) -> str:
    """Golden hash over the canonical JSON form (stable across dict ordering)."""
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_text(canonical)


def vlm_cache_key(*, image_bytes: bytes, prompt: str, model: str) -> str:
    """Single filename-safe key over (image sha256, prompt sha256, model snapshot).

    ``model`` is the snapshot identifier we control (model id / pinned tag) — not
    a cryptographic weights hash; it is recorded verbatim so replays are scoped
    to the exact model string used.
    """
    parts = f"{_sha256_bytes(image_bytes)}\n{_sha256_text(prompt)}\n{model}"
    return _sha256_text(parts)


def build_cache_entry(
    *, image_bytes: bytes, prompt: str, model: str, content: dict[str, Any]
) -> dict[str, Any]:
    """Provenance-carrying cache entry (content + the three hashes + golden hash)."""
    return {
        "image_sha256": _sha256_bytes(image_bytes),
        "prompt_sha256": _sha256_text(prompt),
        "model": model,
        "content": content,
        "content_sha256": content_sha256(content),
    }


def entry_content_if_intact(entry: object) -> dict[str, Any] | None:
    """Return the cached content only if the golden hash matches; else None (fail-closed)."""
    if not isinstance(entry, dict):
        return None
    content = entry.get("content")
    stored_hash = entry.get("content_sha256")
    if not isinstance(content, dict) or not isinstance(stored_hash, str):
        return None
    if content_sha256(content) != stored_hash:
        return None
    return content


class VlmResponseStore(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put(self, key: str, entry: dict[str, Any]) -> None: ...


class InMemoryVlmResponseStore:
    """Process-local store (tests / ephemeral runs)."""

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self._entries.get(key)

    def put(self, key: str, entry: dict[str, Any]) -> None:
        self._entries[key] = entry


__all__ = [
    "InMemoryVlmResponseStore",
    "VlmResponseStore",
    "build_cache_entry",
    "content_sha256",
    "entry_content_if_intact",
    "vlm_cache_key",
]
