from __future__ import annotations

from pathlib import Path


class LocalObjectStore:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir.resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

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
        return target.read_bytes()

    def delete(self, key: str) -> None:
        target = self._resolve_key(key)
        if target.exists() and target.is_file():
            target.unlink()

    def presign_get(self, key: str, *, expires_in_seconds: int = 3600) -> str | None:
        del expires_in_seconds
        target = self._resolve_key(key)
        if not target.exists() or not target.is_file():
            return None
        return target.as_uri()

    def _resolve_key(self, key: str) -> Path:
        normalised = self._normalise_key(key)
        target = (self._base_dir / normalised).resolve()
        if not target.is_relative_to(self._base_dir):
            raise ValueError(f"Object key escapes base directory: {key}")
        return target

    def _normalise_key(self, key: str) -> str:
        return key.strip().replace("\\", "/").lstrip("/")