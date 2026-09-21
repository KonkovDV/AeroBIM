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
_MAX_COMPONENT_LENGTH = 255


def normalize_object_key(key: str) -> str:
    """Return a safe, canonical slash-separated object key.

    This is deliberately stricter than an S3 key (S3 accepts almost anything):
    AeroBIM keys are also used by the local backend and are often tenant-scoped.
    Rejecting ambiguous keys is safer than relying on a backend's interpretation.
    """

    if not isinstance(key, str):
        raise ValueError("Object key must be a string")
    normalized = unicodedata.normalize("NFKC", key.strip().replace("\\", "/"))
    if not normalized or normalized.startswith("/") or _DRIVE_ABS.match(normalized):
        raise ValueError("Object key must be a non-empty relative key")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in normalized):
        raise ValueError("Object key must not contain control characters")

    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Object key must not contain empty or traversal components")
    for part in parts:
        if len(part) > _MAX_COMPONENT_LENGTH:
            raise ValueError("Object key component exceeds maximum length")
        if ":" in part:
            raise ValueError("Object key must not contain colons or NTFS data streams")
        if part[-1] in ". ":
            raise ValueError("Object key components must not end in a dot or space")
        stem = part.split(".", 1)[0].rstrip(" ")
        if stem.upper() in _RESERVED_NAMES:
            raise ValueError(f"Object key uses a reserved Windows device name: {part}")
    return "/".join(parts)


__all__ = ["normalize_object_key"]
