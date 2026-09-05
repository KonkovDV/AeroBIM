"""Storage path jail: resolve user paths without following planted symlinks."""

from __future__ import annotations

import os
import re
import stat
import unicodedata
from pathlib import Path
from typing import IO, Any
from urllib.parse import unquote


class PathJailError(ValueError):
    """Raised when a path escapes the storage root or uses a symlink."""


_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_UNC = re.compile(r"^[\\/]{2}")
_COMPONENT_SPLIT = re.compile(r"[\\/]+")
# Nested percent-encoding (%252e%252e → %2e%2e → ..) must fully decode.
_MAX_PERCENT_DECODE_ROUNDS = 4
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
    # Decode percent-encoding to a fixed point so %252e%252e cannot remain as %2e%2e
    # for a later decoder. Cap rounds so a pathological chain cannot spin.
    decoded = user_path
    for _ in range(_MAX_PERCENT_DECODE_ROUNDS):
        nxt = unquote(decoded)
        if nxt == decoded:
            break
        decoded = nxt
    else:
        raise PathJailError("Percent-encoding nesting exceeds decode limit")
    if "%" in decoded and unquote(decoded) != decoded:
        raise PathJailError("Percent-encoding nesting exceeds decode limit")
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
        if not component or component == ".":
            continue
        if component == "..":
            # Split-level reject: Path.parts misses ".." on POSIX when the
            # vector uses Windows separators ("..\\evil" is one component there).
            # Message keeps the boundary contract pinned by RT phase-4 tests.
            raise PathJailError(f"Path escapes storage boundary: {normalized}")
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


def _windows_open_write_nofollow(path: Path, mode: str) -> IO[Any]:
    """Open for write without following NTFS reparse points (F-01).

    ``path.open`` / ``os.open`` on Windows follow symlinks and can truncate the
    target before a post-open ``is_symlink`` check. ``CreateFileW`` with
    ``FILE_FLAG_OPEN_REPARSE_POINT`` opens the reparse point itself so we can
    refuse it without touching the destination.
    """
    import ctypes
    import msvcrt
    from ctypes import wintypes

    generic_write = 0x40000000
    file_append_data = 0x0004
    file_share_read = 0x1
    file_share_write = 0x2
    file_share_delete = 0x4
    create_new = 1
    open_always = 4
    file_attribute_normal = 0x80
    file_flag_open_reparse_point = 0x00200000
    file_attribute_reparse_point = 0x400

    access = file_append_data if mode == "ab" else generic_write
    creation = create_new if mode == "xb" else open_always

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = ctypes.c_void_p
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = wintypes.BOOL

    class _ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    get_info = kernel32.GetFileInformationByHandle
    get_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(_ByHandleFileInformation)]
    get_info.restype = wintypes.BOOL
    set_pointer = kernel32.SetFilePointer
    set_pointer.argtypes = [ctypes.c_void_p, wintypes.LONG, wintypes.PLONG, wintypes.DWORD]
    set_pointer.restype = wintypes.DWORD
    set_eof = kernel32.SetEndOfFile
    set_eof.argtypes = [ctypes.c_void_p]
    set_eof.restype = wintypes.BOOL

    handle = create_file(
        str(path),
        access,
        file_share_read | file_share_write | file_share_delete,
        None,
        creation,
        file_attribute_normal | file_flag_open_reparse_point,
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle in {None, 0, invalid}:
        err = ctypes.get_last_error()
        # ERROR_FILE_EXISTS / ERROR_ALREADY_EXISTS
        if mode == "xb" and err in {80, 183}:
            raise FileExistsError(str(path))
        raise PathJailError(f"Cannot open storage path without following links: {path}") from None
    handle_int = int(handle)

    info = _ByHandleFileInformation()
    if not get_info(handle, ctypes.byref(info)):
        close_handle(handle)
        raise PathJailError(f"Cannot inspect storage handle: {path}")
    if int(info.dwFileAttributes) & file_attribute_reparse_point:
        close_handle(handle)
        raise PathJailError(f"Symlinks are not allowed in storage paths: {path}")

    if mode == "wb":
        set_pointer(handle, 0, None, 0)
        if not set_eof(handle):
            close_handle(handle)
            raise PathJailError(f"Cannot truncate storage path: {path}")

    flags = getattr(os, "O_BINARY", 0)
    if mode == "ab":
        flags |= getattr(os, "O_APPEND", 0)
    try:
        fd = msvcrt.open_osfhandle(handle_int, flags)
    except OSError as exc:
        close_handle(handle)
        raise PathJailError(f"Cannot open storage path without following links: {path}") from exc
    return os.fdopen(fd, mode)


def _open_write_fallback(path: Path, *, base: Path, mode: str) -> IO[Any]:
    """lstat + open retry when O_NOFOLLOW / Windows reparse open is unavailable."""

    last_error: Exception | None = None
    for _ in range(3):
        reject_symlinks(path, base=base)
        try:
            st = path.lstat()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise PathJailError(f"Cannot stat storage path: {path}") from exc
        else:
            if stat.S_ISLNK(st.st_mode):
                raise PathJailError(f"Symlinks are not allowed in storage paths: {path}")
        handle = path.open(mode)
        try:
            reject_symlinks(path, base=base)
            if path.is_symlink():
                raise PathJailError(f"Symlinks are not allowed in storage paths: {path}")
        except Exception as exc:
            handle.close()
            last_error = exc
            continue
        return handle
    if last_error is not None:
        raise last_error
    raise PathJailError(f"Cannot open storage path without following links: {path}")


def open_storage_file(path: Path, *, base: Path, mode: str = "rb") -> IO[Any]:
    """Open a storage file after symlink rejection; prefer O_NOFOLLOW on POSIX.

    Callers must pass a path already resolved under *base* (or about to be checked).
    Re-checks for planted symlinks immediately before open to shrink TOCTOU windows.
    On Windows, write modes use ``CreateFileW`` + ``FILE_FLAG_OPEN_REPARSE_POINT``
    so a raced symlink is not truncated before the post-open check (F-01).
    """
    reject_symlinks(path, base=base)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if mode == "rb" and nofollow:
        try:
            fd = os.open(str(path), os.O_RDONLY | nofollow)
        except OSError as exc:
            raise PathJailError(
                f"Cannot open storage path without following links: {path}"
            ) from exc
        return os.fdopen(fd, mode)
    write_flags = {
        "wb": os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        "ab": os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        "xb": os.O_WRONLY | os.O_CREAT | os.O_EXCL,
    }
    if mode in write_flags and nofollow:
        try:
            fd = os.open(str(path), write_flags[mode] | nofollow, 0o644)
        except OSError as exc:
            raise PathJailError(
                f"Cannot open storage path without following links: {path}"
            ) from exc
        return os.fdopen(fd, mode)

    if mode in write_flags and os.name == "nt":
        try:
            return _windows_open_write_nofollow(path, mode)
        except PathJailError:
            raise
        except FileExistsError:
            raise
        except OSError as exc:
            raise PathJailError(
                f"Cannot open storage path without following links: {path}"
            ) from exc

    if mode in write_flags:
        return _open_write_fallback(path, base=base, mode=mode)

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
