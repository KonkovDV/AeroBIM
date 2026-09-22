"""Collect PackageFileEntry rows from hashes already stored on the request.

Does not read file bytes and does not stat the disk. ValidationRequest has
no hash field for the IFC or IDS path, so those files are omitted until one
exists. An empty result must not be passed to compute_package_id.
"""

from __future__ import annotations

from typing import TypeGuard

from aerobim.domain.models import DrawingSource, RequirementSource, ValidationRequest
from aerobim.domain.package_manifest import (
    Discipline,
    FileRole,
    PackageFileEntry,
    UploadState,
)


def _sha256_known(value: str | None) -> TypeGuard[str]:
    if value is None or len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def _entry(
    *,
    logical_path: str,
    sha256: str,
    media_type: str,
    role: FileRole,
    revision: str | None,
    source: str | None,
) -> PackageFileEntry:
    return PackageFileEntry(
        logical_path=logical_path,
        sha256=sha256.lower(),
        size=0,
        media_type=media_type,
        role=role,
        discipline=Discipline.UNKNOWN,
        revision=revision,
        source=source,
        upload_state=UploadState.COMPLETE,
    )


def _drawing_role(source: DrawingSource) -> FileRole:
    fmt = (source.format or "").strip().lower()
    path = source.path
    suffix = path.suffix.lower() if path is not None else ""
    if fmt == "dxf" or suffix == ".dxf":
        return FileRole.DRAWING_DXF
    return FileRole.DRAWING_PDF


def _drawing_media_type(source: DrawingSource) -> str:
    path = source.path
    if path is None:
        return "application/octet-stream"
    return {
        ".pdf": "application/pdf",
        ".dxf": "image/vnd.dxf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


def _from_named_source(
    source: RequirementSource | None,
    *,
    role: FileRole,
    media_type: str,
    revision: str | None,
) -> PackageFileEntry | None:
    if source is None or source.path is None or not _sha256_known(source.sha256):
        return None
    return _entry(
        logical_path=source.path.name,
        sha256=source.sha256,
        media_type=media_type,
        role=role,
        revision=source.revision or revision,
        source=source.source_id,
    )


def collect_file_entries(request: ValidationRequest) -> tuple[PackageFileEntry, ...]:
    """Entries for sources that already carry a 64-character sha256."""
    revision = (request.revision or "").strip() or None
    entries: list[PackageFileEntry] = []
    for source, role, media_type in (
        (request.requirement_source, FileRole.SPECIFICATION_TEXT, "text/plain"),
        (request.technical_spec_source, FileRole.SPECIFICATION_TEXT, "text/plain"),
        (request.calculation_source, FileRole.CALCULATION, "application/octet-stream"),
    ):
        entry = _from_named_source(
            source,
            role=role,
            media_type=media_type,
            revision=revision,
        )
        if entry is not None:
            entries.append(entry)

    for drawing in request.drawing_sources:
        digest = drawing.sha256
        path = drawing.path
        if path is None or not _sha256_known(digest):
            continue
        entries.append(
            _entry(
                logical_path=path.name,
                sha256=digest,
                media_type=_drawing_media_type(drawing),
                role=_drawing_role(drawing),
                revision=drawing.revision or revision,
                source=drawing.sheet_id,
            )
        )
    return tuple(entries)


__all__ = ["collect_file_entries"]
