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
from pathlib import Path
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


class FilesystemVlmResponseStore:
    """JSON-per-key store; the key is a sha256 hex (safe filename, no traversal)."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _path(self, key: str) -> Path:
        return self._root / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            loaded = json.loads(self._path(key).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return loaded if isinstance(loaded, dict) else None

    def put(self, key: str, entry: dict[str, Any]) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path(key)
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
    ) -> None:
        self._reader = reader
        self._store = store
        self._model = model
        self._provenance = {
            "endpoint": endpoint,
            "request_schema_hash": request_schema_hash,
            "provider_snapshot": provider_snapshot,
            "normalizer_version": normalizer_version,
        }

    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> KimiReadResult:
        key = vlm_cache_key(image_bytes=image_bytes, prompt=prompt, model=self._model)
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
        result = self._reader.read_region(
            image_bytes,
            media_type=media_type,
            sheet_id=sheet_id,
            region_id=region_id,
            prompt=prompt,
        )
        self._store.put(
            key,
            build_cache_entry(
                image_bytes=image_bytes,
                prompt=prompt,
                model=self._model,
                content=result.content,
                provenance=self._provenance,
            ),
        )
        return result


__all__ = ["CachingVlmReader", "FilesystemVlmResponseStore"]
