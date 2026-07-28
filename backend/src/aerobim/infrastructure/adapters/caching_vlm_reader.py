"""§2.1 caching VLM reader — deterministic act-grade replay wrapper.

Wraps any region reader (``read_region``) with a response store keyed by
``sha256(image) + sha256(prompt) + model``. On a cache HIT the stored content is
returned WITHOUT a network call (``determinism_basis="vlm_cache_replay"``) after
verifying the golden content hash; on a MISS the underlying reader is called and
the response is persisted for future replay. Fail-closed: a corrupt / tampered
entry is ignored and treated as a miss. Advisory-only — never on the verdict path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter, time
from typing import Any, Protocol

from aerobim.domain.vlm_cache import (
    VlmResponseStore,
    build_cache_entry,
    entry_content_if_intact,
    entry_matches_request,
    vlm_cache_key,
)
from aerobim.domain.vlm_normalize import NORMALIZER_VERSION
from aerobim.infrastructure.adapters.kimi_k3_advisory_client import KimiReadResult


class _RegionReader(Protocol):
    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> KimiReadResult: ...


_SHA256_HEX_LEN = 64
_HEX_CHARS = frozenset("0123456789abcdef")


def _is_cache_key_safe(key: str) -> bool:
    """A store key MUST be a sha256 hex digest — no separators / traversal / dots."""
    return len(key) == _SHA256_HEX_LEN and all(ch in _HEX_CHARS for ch in key)


class FilesystemVlmResponseStore:
    """JSON-per-key store, fail-closed (§5.9–§5.11).

    Keys must be sha256 hex (rejects path traversal via the key); a symlinked
    target is refused (never followed for read or write); entries older than
    ``ttl_seconds`` are treated as a miss and deleted (explicit deletion policy);
    the cache dir is created owner-only (best-effort; a no-op ACL on Windows).
    """

    def __init__(self, root: Path, *, ttl_seconds: float | None = None) -> None:
        self._root = Path(root)
        self._ttl_seconds = ttl_seconds

    def _path(self, key: str) -> Path | None:
        if not _is_cache_key_safe(key):
            return None
        return self._root / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if path is None or path.is_symlink():  # bad key / planted symlink -> miss
            return None
        try:
            if self._ttl_seconds is not None and path.exists():
                if (time() - path.stat().st_mtime) > self._ttl_seconds:
                    path.unlink(missing_ok=True)  # expired -> deletion policy
                    return None
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return loaded if isinstance(loaded, dict) else None

    def put(self, key: str, entry: dict[str, Any]) -> None:
        path = self._path(key)
        if path is None:
            return  # fail-closed: never write under an unsafe key
        self._root.mkdir(parents=True, exist_ok=True)
        try:
            self._root.chmod(0o700)  # owner-only; best-effort (Windows ACLs differ)
        except OSError:
            pass
        if path.is_symlink():  # never write through a planted symlink
            return
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(entry, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
        )
        tmp.replace(path)  # atomic publish


class CachingVlmReader:
    """Region reader that caches responses for deterministic replay (§2.1)."""

    def __init__(
        self,
        reader: _RegionReader,
        store: VlmResponseStore,
        *,
        model: str,
        endpoint: str = "",
        request_schema_hash: str = "",
        provider_snapshot: str = "",
        normalizer_version: str = NORMALIZER_VERSION,
        reasoning_effort: str = "",
        cache_namespace: str = "",
        cache_project: str = "",
    ) -> None:
        self._reader = reader
        self._store = store
        self._model = model
        self._reasoning_effort = reasoning_effort
        # Isolation scope folded into the key (e.g. tenant + project). The advisory
        # contour is not yet tenant-aware; a tenant-scoped consumer MUST pass its
        # tenant (and optional project) here so cache entries never cross tenants.
        self._namespace = cache_namespace
        self._project = cache_project
        self._provenance = {
            "endpoint": endpoint,
            "request_schema_hash": request_schema_hash,
            "provider_snapshot": provider_snapshot,
            "normalizer_version": normalizer_version,
        }

    def _key(self, image_bytes: bytes, prompt: str) -> str:
        return vlm_cache_key(
            image_bytes=image_bytes,
            prompt=prompt,
            model=self._model,
            namespace=self._namespace,
            project=self._project,
            request_schema_hash=self._provenance["request_schema_hash"],
            normalizer_version=self._provenance["normalizer_version"],
            reasoning_effort=self._reasoning_effort,
        )

    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> KimiReadResult:
        key = self._key(image_bytes, prompt)
        entry = self._store.get(key)
        cached = entry_content_if_intact(entry)
        # Two-layer integrity: golden content hash AND the entry's request hashes
        # must match THIS (image, prompt, model) — else fail closed to a miss.
        if cached is not None and entry_matches_request(
            entry, image_bytes=image_bytes, prompt=prompt, model=self._model
        ):
            return KimiReadResult(
                content=cached, usage={"cache": "hit"}, determinism_basis="vlm_cache_replay"
            )
        started = perf_counter()
        result = self._reader.read_region(
            image_bytes,
            media_type=media_type,
            sheet_id=sheet_id,
            region_id=region_id,
            prompt=prompt,
        )
        latency_ms = round((perf_counter() - started) * 1000.0, 3)
        self._store.put(
            key,
            build_cache_entry(
                image_bytes=image_bytes,
                prompt=prompt,
                model=self._model,
                content=result.content,
                provenance=self._provenance,
                usage=result.usage,
                latency_ms=latency_ms,
                recorded_at=datetime.now(tz=UTC).isoformat(),
                namespace=self._namespace,
                reasoning_effort=self._reasoning_effort,
            ),
        )
        return result


__all__ = ["CachingVlmReader", "FilesystemVlmResponseStore"]
