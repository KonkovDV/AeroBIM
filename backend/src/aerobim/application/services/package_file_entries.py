"""Build PackageFileEntry tuples from a ValidationRequest.

Only produces entries for files where sha256 is already known.
Never hashes files at analysis time.

Design rules
------------
- Pure function: no I/O, no side effects, deterministic output.
- Unknown sha256 (None or empty) → entry skipped.
- Missing size → 0 (size=0 is honest; it does not break compute_package_id
  because package_id depends on sha256, not size).
- Fixture / dev runs that omit sha256 get an empty tuple; the caller
  (build_evidence_records) falls back to sha256(request_id).
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import DrawingSource, ValidationRequest
from aerobim.domain.package_manifest import (
    Discipline,
    FileRole,
    PackageFileEntry,
    UploadState,
)


def _drawing_role(source: DrawingSource) -> FileRole:
    fmt = (source.format or "").strip().lower()
    if fmt == "dxf" or (
        source.path is not None and source.path.suffix.lower() == ".dxf"
    ):
        return FileRole.DRAWING_DXF
    return FileRole.DRAWING_PDF


def _drawing_media_type(source: DrawingSource) -> str:
    if source.path is None:
        return "application/octet-stream"
    suffix = source.path.suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".dxf": "image/vnd.dxf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    return mapping.get(suffix, "application/octet-stream")


def _file_size(path: Path | None) -> int:
    """Try to read file size without opening. Returns 0 when unavailable."""
    if path is None:
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _sha256_known(value: str | None) -> bool:
    return bool(value and len(value) >= 16)


def collect_file_entries(
    request: ValidationRequest,
) -> tuple[PackageFileEntry, ...]:
    """Return PackageFileEntry for every file whose sha256 is already known.

    Parameters
    ----------
    request:
        The analysis request. sha256 fields are read from DrawingSource.sha256
        and, when present, from request.ifc_sha256 / request.ids_sha256.

    Returns
    -------
    Tuple of PackageFileEntry. Empty when no sha256 values are available
    (fixture / dev / document-only runs). The caller must handle the empty
    case — do not call PackageManifest.compute_package_id with an empty list.
    """
    entries: list[PackageFileEntry] = []
    revision = (request.revision or "").strip() or None

    # --- IFC model -------------------------------------------------------
    ifc_sha256: str | None = getattr(request, "ifc_sha256", None)
    if request.ifc_path is not None and _sha256_known(ifc_sha256):
        assert ifc_sha256 is not None  # narrowed above
        entries.append(
            PackageFileEntry(
                logical_path=str(request.ifc_path.name),
                sha256=ifc_sha256,
                size=_file_size(request.ifc_path),
                media_type="application/x-step",
                role=FileRole.IFC_MODEL,
                discipline=Discipline.UNKNOWN,
                revision=revision,
                source=str(request.ifc_path),
                upload_state=UploadState.COMPLETE,
            )
        )

    # --- IDS specification -----------------------------------------------
    ids_sha256: str | None = getattr(request, "ids_sha256", None)
    if request.ids_path is not None and _sha256_known(ids_sha256):
        assert ids_sha256 is not None
        entries.append(
            PackageFileEntry(
                logical_path=str(request.ids_path.name),
                sha256=ids_sha256,
                size=_file_size(request.ids_path),
                media_type="application/xml",
                role=FileRole.IDS_SPECIFICATION,
                discipline=Discipline.UNKNOWN,
                revision=revision,
                source=str(request.ids_path),
                upload_state=UploadState.COMPLETE,
            )
        )

    # --- Drawing sources -------------------------------------------------
    for source in request.drawing_sources:
        if not _sha256_known(source.sha256) or source.path is None:
            continue
        assert source.sha256 is not None
        entries.append(
            PackageFileEntry(
                logical_path=str(source.path.name),
                sha256=source.sha256,
                size=_file_size(source.path),
                media_type=_drawing_media_type(source),
                role=_drawing_role(source),
                discipline=Discipline.UNKNOWN,
                revision=source.revision or revision,
                source=source.source_id or str(source.path),
                upload_state=UploadState.COMPLETE,
            )
        )

    # --- Norm rule packs -------------------------------------------------
    for pack_path in (request.norm_rule_pack_paths or ()):
        pack_sha256: str | None = None
        # Norm packs may carry sha256 as a sidecar attribute.
        # Absent that, we skip: hashing at analysis time is not allowed.
        pack_sha256 = getattr(pack_path, "sha256", None)
        if not _sha256_known(pack_sha256):
            continue
        assert pack_sha256 is not None
        p = Path(str(pack_path))
        entries.append(
            PackageFileEntry(
                logical_path=p.name,
                sha256=pack_sha256,
                size=_file_size(p),
                media_type="application/zip",
                role=FileRole.NORM_PACK,
                discipline=Discipline.UNKNOWN,
                revision=None,
                source=str(pack_path),
                upload_state=UploadState.COMPLETE,
            )
        )

    return tuple(entries)


__all__ = ["collect_file_entries"]
