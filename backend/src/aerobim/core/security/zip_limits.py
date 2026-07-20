"""ZIP member limits — decompression-bomb protection for uploads."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_MEMBERS = 256
DEFAULT_MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_MEMBER_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_COMPRESSION_RATIO = 100.0
DEFAULT_MAX_ARCHIVE_FILE_BYTES = 512 * 1024 * 1024


class ZipBombError(ValueError):
    """Raised when a ZIP archive exceeds safe expansion limits."""


@dataclass(frozen=True)
class ZipInspection:
    member_count: int
    total_uncompressed_bytes: int
    max_member_bytes: int
    max_ratio: float


def _inspect_zipfile(
    archive: zipfile.ZipFile,
    *,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> ZipInspection:
    """Inspect ZIP central directory without extracting member payloads."""

    infos = archive.infolist()
    if len(infos) > max_members:
        raise ZipBombError(f"ZIP has too many members ({len(infos)} > {max_members})")

    total = 0
    max_member = 0
    max_ratio = 0.0
    for info in infos:
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        if name.startswith("/") or name.startswith("../") or "/../" in f"/{name}/":
            raise ZipBombError(f"ZIP member path is not allowed: {info.filename!r}")
        if ":" in name.split("/")[0]:
            # Windows drive / alternate stream style absolute members
            raise ZipBombError(f"ZIP member path is not allowed: {info.filename!r}")
        size = int(info.file_size)
        compress = max(int(info.compress_size), 1)
        if size > max_member_bytes:
            raise ZipBombError(
                f"ZIP member {info.filename!r} too large ({size} > {max_member_bytes})"
            )
        ratio = size / compress
        if ratio > max_compression_ratio and size > 1024 * 1024:
            raise ZipBombError(
                f"ZIP member {info.filename!r} compression ratio too high ({ratio:.1f})"
            )
        total += size
        max_member = max(max_member, size)
        max_ratio = max(max_ratio, ratio)
        if total > max_uncompressed_bytes:
            raise ZipBombError(
                f"ZIP uncompressed size too large ({total} > {max_uncompressed_bytes})"
            )
    return ZipInspection(
        member_count=len(infos),
        total_uncompressed_bytes=total,
        max_member_bytes=max_member,
        max_ratio=max_ratio,
    )


def inspect_zip_bytes(
    payload: bytes,
    *,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
) -> ZipInspection:
    """Inspect ZIP central directory from an in-memory payload."""

    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            return _inspect_zipfile(
                archive,
                max_members=max_members,
                max_uncompressed_bytes=max_uncompressed_bytes,
                max_member_bytes=max_member_bytes,
                max_compression_ratio=max_compression_ratio,
            )
    except zipfile.BadZipFile as exc:
        raise ZipBombError(f"Invalid ZIP archive: {exc}") from exc


def inspect_zip_path(
    path: Path,
    *,
    max_members: int = DEFAULT_MAX_MEMBERS,
    max_uncompressed_bytes: int = DEFAULT_MAX_UNCOMPRESSED_BYTES,
    max_member_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
    max_archive_file_bytes: int = DEFAULT_MAX_ARCHIVE_FILE_BYTES,
) -> ZipInspection:
    """Inspect ZIP central directory from a filesystem path without loading whole file."""

    try:
        archive_size = path.stat().st_size
    except OSError as exc:
        raise ZipBombError(f"ZIP archive is not readable: {exc}") from exc
    if archive_size > max_archive_file_bytes:
        raise ZipBombError(
            f"ZIP archive file too large ({archive_size} > {max_archive_file_bytes})"
        )
    try:
        with zipfile.ZipFile(path, "r") as archive:
            return _inspect_zipfile(
                archive,
                max_members=max_members,
                max_uncompressed_bytes=max_uncompressed_bytes,
                max_member_bytes=max_member_bytes,
                max_compression_ratio=max_compression_ratio,
            )
    except zipfile.BadZipFile as exc:
        raise ZipBombError(f"Invalid ZIP archive: {exc}") from exc


__all__ = [
    "DEFAULT_MAX_ARCHIVE_FILE_BYTES",
    "DEFAULT_MAX_COMPRESSION_RATIO",
    "DEFAULT_MAX_MEMBER_BYTES",
    "DEFAULT_MAX_MEMBERS",
    "DEFAULT_MAX_UNCOMPRESSED_BYTES",
    "ZipBombError",
    "ZipInspection",
    "inspect_zip_bytes",
    "inspect_zip_path",
]
