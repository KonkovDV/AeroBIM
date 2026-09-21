"""Canonical object-key validation for filesystem and S3 stores.

Object-store keys are not OS paths, but they still cross tenant and storage
boundaries. Keep one canonical representation so ``..``, absolute keys,
Windows ADS syntax, and Unicode/control-character tricks cannot bypass a
store-specific prefix or produce ambiguous keys.
"""

from __future__ import annotations

import re
import unicodedata

_DRIVE_ABS = re.compile(r"^[A-Za-z]:[\\/]")
_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
_MAX_COMPONENT_BYTES = 255
_MAX_KEY_BYTES = 1024


def normalize_object_key(key: str) -> str:
    """Return a safe, canonical slash-separated object key.

    This is deliberately stricter than an S3 key (S3 accepts almost anything):
    AeroBIM keys are also used by the local backend and are often tenant-scoped.
    Rejecting ambiguous keys is safer than relying on a backend's interpretation.
    Length limits are measured after canonicalization in UTF-8 bytes, matching
    storage protocol and filesystem boundaries rather than Python characters.
    """

    if not isinstance(key, str):
        raise ValueError("Object key must be a string")
    normalized = unicodedata.normalize("NFKC", key.strip().replace("\\", "/"))
    if not normalized or normalized.startswith("/") or _DRIVE_ABS.match(normalized):
        raise ValueError("Object key must be a non-empty relative key")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        raise ValueError("Object key must not contain control characters")
    try:
        encoded_key = normalized.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("Object key must be valid UTF-8") from exc
    if len(encoded_key) > _MAX_KEY_BYTES:
        raise ValueError("Object key exceeds maximum UTF-8 byte length")

    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Object key must not contain empty or traversal components")
    for part in parts:
        if len(part.encode("utf-8")) > _MAX_COMPONENT_BYTES:
            raise ValueError("Object key component exceeds maximum UTF-8 byte length")
        if ":" in part:
            raise ValueError("Object key must not contain colons or NTFS data streams")
        if part[-1] in ". ":
            raise ValueError("Object key components must not end in a dot or space")
        stem = part.split(".", 1)[0].rstrip(" ")
        if stem.upper() in _RESERVED_NAMES:
            raise ValueError(f"Object key uses a reserved Windows device name: {part}")
    return "/".join(parts)


__all__ = ["normalize_object_key"]
