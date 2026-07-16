"""Storage path jail: resolve user paths without following planted symlinks."""

from __future__ import annotations

from pathlib import Path


class PathJailError(ValueError):
    """Raised when a path escapes the storage root or uses a symlink."""


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
    base_resolved = base.resolve()
    raw = Path(user_path)
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
