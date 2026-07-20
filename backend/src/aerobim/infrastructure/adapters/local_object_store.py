from __future__ import annotations

from pathlib import Path

from aerobim.core.security.object_limits import (
    DEFAULT_GET_CHUNK_BYTES,
    DEFAULT_MAX_GET_BYTES,
    ObjectTooLargeError,
)
from aerobim.core.security.path_jail import PathJailError, reject_symlinks


class LocalObjectStore:
    def __init__(
        self,
        base_dir: Path,
        *,
        max_get_bytes: int = DEFAULT_MAX_GET_BYTES,
    ) -> None:
        self._base_dir = base_dir.resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._max_get_bytes = max_get_bytes

    def put_bytes(
        self,
        key: str,
        payload: bytes,
        *,
        content_type: str | None = None,
    ) -> str:
        del content_type
        target = self._resolve_key(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return self._normalise_key(key)

    def get_bytes(self, key: str) -> bytes | None:
        target = self._resolve_key(key)
        if not target.exists() or not target.is_file():
            return None
        size = target.stat().st_size
        if size > self._max_get_bytes:
            raise ObjectTooLargeError(f"Object file too large ({size} > {self._max_get_bytes})")
        chunks: list[bytes] = []
        total = 0
        with target.open("rb") as handle:
            while True:
                chunk = handle.read(DEFAULT_GET_CHUNK_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > self._max_get_bytes:
                    raise ObjectTooLargeError(
                        f"Object payload too large (>{self._max_get_bytes} bytes)"
                    )
                chunks.append(chunk)
        return b"".join(chunks)

    def delete(self, key: str) -> None:
        target = self._resolve_key(key)
        if target.exists() and target.is_file():
            target.unlink()

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None:
        # Local residual: returns file:// URI — caller opens the path directly;
        # max_get_bytes is enforced only on get_bytes().
        del expires_in_seconds
        target = self._resolve_key(key)
        if not target.exists() or not target.is_file():
            return None
        return target.as_uri()

    def _resolve_key(self, key: str) -> Path:
        normalised = self._normalise_key(key)
        candidate = self._base_dir / normalised
        try:
            reject_symlinks(candidate, base=self._base_dir)
        except PathJailError as exc:
            raise ValueError(str(exc)) from exc
        target = candidate.resolve()
        if not target.is_relative_to(self._base_dir):
            raise ValueError(f"Object key escapes base directory: {key}")
        return target

    def _normalise_key(self, key: str) -> str:
        return key.strip().replace("\\", "/").lstrip("/")


__all__ = ["ObjectTooLargeError", "LocalObjectStore"]
