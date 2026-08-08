"""Storage path jail: resolve user paths without following planted symlinks."""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import IO, Any
from urllib.parse import unquote


class PathJailError(ValueError):
    """Raised when a path escapes the storage root or uses a symlink."""


_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_UNC = re.compile(r"^[\\/]{2}")
_COMPONENT_SPLIT = re.compile(r"[\\/]+")
# NTFS filename component limit; also bounds the 8.3/long-path expansion surface.
_MAX_COMPONENT_LENGTH = 255
# Reserved device names are dangerous in ANY component, with or without extension
# (``NUL.txt`` still resolves to the NUL device on Windows).
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{digit}" for digit in range(1, 10)}
    | {f"LPT{digit}" for digit in range(1, 10)}
)


def _normalize_user_path(user_path: str) -> str:
    if "\x00" in user_path:
        raise PathJailError("Null bytes are not allowed in paths")
    if any(ord(ch) < 32 for ch in user_path):
        raise PathJailError("Control characters are not allowed in paths")
    # Decode a single layer of percent-encoding so %2e%2e / %2f cannot bypass checks.
    decoded = unquote(user_path)
    if "\x00" in decoded or any(ord(ch) < 32 for ch in decoded):
        raise PathJailError("Encoded control characters are not allowed in paths")
    # NFKC collapses compatibility lookalikes before jail checks (OWASP API1 / Unicode).
    return unicodedata.normalize("NFKC", decoded)


def _validate_path_components(normalized: str) -> None:
    """Reject Windows-hostile components: ADS colons, device names, overlong parts.

    Runs after the UNC / drive-absolute layer so those keep their specific
    messages; storage-relative paths never legitimately contain colons
    (``safe_storage_token`` encodes ``:`` as ``!3a``).
    """
    for component in _COMPONENT_SPLIT.split(normalized):
        if not component or component in (".", ".."):
            continue
        if ":" in component:
            # NTFS alternate data streams: evil.png::$DATA / evil.txt:hidden.
            raise PathJailError("Colons / NTFS data streams are not allowed in paths")
        if len(component) > _MAX_COMPONENT_LENGTH:
            raise PathJailError("Path component exceeds maximum length")
        if component[-1] in ". ":
            # Windows silently strips trailing dots/spaces -> name collisions.
            raise PathJailError("Trailing dots or spaces are not allowed in path components")
        stem = component.split(".", 1)[0].rstrip(" ")
        if stem.upper() in _WINDOWS_RESERVED_NAMES:
            raise PathJailError(f"Windows reserved device name is not allowed: {component}")


def reject_symlinks(path: Path, *, base: Path) -> None:
    """Reject *path* if any component under *base* is a symlink."""
    base_resolved = base.resolve()
    walk_root = base_resolved
    try:
        relative = path.relative_to(base_resolved)
    except ValueError:
        # Windows may expose the same directory as short (8.3) and long forms.
        # Prefer parts relative to the caller-supplied base, then walk under resolve().
        try:
            base_abs = base.absolute()
            path_abs = path.absolute() if path.is_absolute() else (base_abs / path).absolute()
            relative = path_abs.relative_to(base_abs)
        except ValueError as exc:
            raise PathJailError(f"Path escapes storage boundary: {path}") from exc

    if ".." in relative.parts:
        raise PathJailError(f"Path escapes storage boundary: {path}")

    cursor = walk_root
    for part in relative.parts:
        if part in ("", "."):
            continue
        cursor = cursor / part
        if cursor.is_symlink():
            raise PathJailError(f"Symlinks are not allowed in storage paths: {cursor}")


def sanitize_upload_filename(filename: str, *, max_length: int = 180) -> str:
    """Normalize a single upload filename component (not a storage path)."""

    segment = _normalize_user_path(filename.replace("\\", "/").split("/")[-1]).strip()
    if not segment or segment in {".", ".."}:
        segment = "upload.bin"
    for banned in ':*?"<>|\r\n;':
        segment = segment.replace(banned, "")
    segment = "".join(ch for ch in segment if unicodedata.category(ch) not in {"Cf", "Cc"})
    segment = segment.strip(" .") or "upload.bin"
    if len(segment) > max_length:
        segment = segment[:max_length]
    stem = segment.split(".", 1)[0].rstrip(" ")
    if stem.upper() in _WINDOWS_RESERVED_NAMES:
        segment = f"_{segment}"
    return segment


def safe_storage_token(value: str) -> str:
    """Encode a tenant / pack token as a single reversible path segment.

    Alphanumeric plus ``_-`` are kept; ``.`` and other specials become ``!{ord:02x}``
    so ``Tenant/A`` and ``Tenant_A`` never collide, and ``.`` / ``..`` cannot escape
    storage joins. Input is NFKC-normalized first.
    """
    if "\x00" in value:
        raise PathJailError("Null bytes are not allowed in storage tokens")
    normalized = unicodedata.normalize("NFKC", value.strip())
    if not normalized or normalized in {".", ".."}:
        raise PathJailError("Empty or path-traversal storage token is not allowed")
    encoded: list[str] = []
    for ch in normalized:
        # Keep alnum + _- only; encode '.' so ".." cannot survive as a path segment.
        if ch.isalnum() or ch in "_-":
            encoded.append(ch)
        else:
            encoded.append(f"!{ord(ch):02x}")
    safe = "".join(encoded)
    if not safe or safe in {".", ".."}:
        raise PathJailError("Empty or path-traversal storage token is not allowed")
    return safe


def open_storage_file(path: Path, *, base: Path, mode: str = "rb") -> IO[Any]:
    """Open a storage file after symlink rejection; prefer O_NOFOLLOW on POSIX.

    Callers must pass a path already resolved under *base* (or about to be checked).
    Re-checks for planted symlinks immediately before open to shrink TOCTOU windows.
    """
    reject_symlinks(path, base=base)
    if mode == "rb" and hasattr(os, "O_NOFOLLOW"):
        try:
            fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
        except OSError as exc:
            raise PathJailError(
                f"Cannot open storage path without following links: {path}"
            ) from exc
        return os.fdopen(fd, mode)

    handle = path.open(mode)
    try:
        reject_symlinks(path, base=base)
        if path.is_symlink():
            raise PathJailError(f"Symlinks are not allowed in storage paths: {path}")
    except Exception:
        handle.close()
        raise
    return handle


def tenant_storage_prefix(tenant_id: str) -> str:
    """Return ``tenants/{safe}/`` for ACL-scoped storage paths."""
    safe = safe_storage_token(tenant_id.strip())
    return f"tenants/{safe}/"


def assert_path_under_tenant_prefix(
    resolved: Path,
    *,
    base: Path,
    tenant_id: str,
) -> None:
    """Reject resolved paths outside the caller's tenant storage prefix."""
    base_resolved = base.resolve()
    try:
        relative = resolved.resolve().relative_to(base_resolved).as_posix()
    except ValueError as exc:
        raise PathJailError(f"Path escapes storage boundary: {resolved}") from exc
    prefix = tenant_storage_prefix(tenant_id)
    if not relative.startswith(prefix):
        raise PathJailError(f"Path outside tenant storage prefix ({prefix}): {relative}")


def resolve_storage_path(user_path: str, *, base: Path) -> Path:
    """Resolve *user_path* strictly under *base*, rejecting escapes and symlinks."""
    if not isinstance(user_path, str) or not user_path.strip():
        raise PathJailError("Empty paths are not allowed")

    normalized = _normalize_user_path(user_path.strip())
    if _UNC.match(normalized) or _DRIVE_ABS.match(normalized):
        raise PathJailError("Absolute / UNC paths are not allowed; use storage-relative paths")
    _validate_path_components(normalized)

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


def resolve_repo_relative_path(user_path: str, *, repo_root: Path) -> Path:
    """Resolve project-relative IFC/matrix paths under *repo_root* (MEP scope jail)."""

    return resolve_storage_path(user_path, base=repo_root)


__all__ = [
    "PathJailError",
    "assert_path_under_tenant_prefix",
    "open_storage_file",
    "reject_symlinks",
    "resolve_repo_relative_path",
    "resolve_storage_path",
    "safe_storage_token",
    "tenant_storage_prefix",
]
