"""Storage path jail: resolve user paths without following planted symlinks."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


class PathJailError(ValueError):
    """Raised when a path escapes the storage root or uses a symlink."""


_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_UNC = re.compile(r"^[\\/]{2}")


def _normalize_user_path(user_path: str) -> str:
    if "\x00" in user_path:
        raise PathJailError("Null bytes are not allowed in paths")
    if any(ord(ch) < 32 for ch in user_path):
        raise PathJailError("Control characters are not allowed in paths")
    # Decode a single layer of percent-encoding so %2e%2e / %2f cannot bypass checks.
    decoded = unquote(user_path)
    if "\x00" in decoded or any(ord(ch) < 32 for ch in decoded):
        raise PathJailError("Encoded control characters are not allowed in paths")
    return decoded


def reject_symlinks(path: Path, *, base: Path) -> None:
    """Reject *path* if any component under *base* is a symlink."""
    base_resolved = base.resolve()
    try:
        relative = path.relative_to(base_resolved)
    except ValueError as exc:
        raise PathJailError(f"Path escapes storage boundary: {path}") from exc

    if ".." in relative.parts:
        raise PathJailError(f"Path escapes storage boundary: {path}")

    cursor = base_resolved
    for part in relative.parts:
        if part in ("", "."):
            continue
        cursor = cursor / part
        if cursor.is_symlink():
            raise PathJailError(f"Symlinks are not allowed in storage paths: {cursor}")


def resolve_storage_path(user_path: str, *, base: Path) -> Path:
    """Resolve *user_path* strictly under *base*, rejecting escapes and symlinks."""
    if not isinstance(user_path, str) or not user_path.strip():
        raise PathJailError("Empty paths are not allowed")

    normalized = _normalize_user_path(user_path.strip())
    if _UNC.match(normalized) or _DRIVE_ABS.match(normalized):
        raise PathJailError("Absolute / UNC paths are not allowed; use storage-relative paths")

    base_resolved = base.resolve()
    raw = Path(normalized)
    if raw.is_absolute():
        raise PathJailError("Absolute paths are not allowed; use storage-relative paths")
    if ".." in raw.parts:
        raise PathJailError(f"Path escapes storage boundary: {user_path}")

    candidate = base_resolved.joinpath(*raw.parts)
    reject_symlinks(candidate, base=base_resolved)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise PathJailError(f"Path escapes storage boundary: {user_path}")
    return resolved
