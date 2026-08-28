"""Upload content sniffing: extension + magic-byte agreement (no libmagic).

Detects common AeroBIM pilot formats from the first bytes. Mismatch between
declared extension and sniffed kind is rejected for binary formats.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

# Enough for ZIP/PDF/PNG/JPEG/DWG and IFC header search.
_SNIFF_WINDOW = 4096

_PDF = b"%PDF"
_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"
_ZIP = b"PK\x03\x04"
_ZIP_EMPTY = b"PK\x05\x06"
_GIF = b"GIF8"
_IFC_MARKERS = (b"ISO-10303-21", b"ISO 10303-21")
_DWG_MARKERS = (b"AC10", b"AC1.")  # AutoCAD DWG version markers


@dataclass(frozen=True)
class SniffResult:
    kind: str
    """Canonical kind: pdf|png|jpeg|gif|zip|ifc|dxf|dwg|xml|json|text|unknown|empty."""
    mime: str
    confidence: str  # high|medium|low


class UploadContentError(ValueError):
    """Raised when upload content does not match declared type or is disallowed."""


def sniff_content(payload: bytes) -> SniffResult:
    """Infer content kind from magic bytes / textual headers."""

    if not payload:
        return SniffResult(kind="empty", mime="application/octet-stream", confidence="high")

    head = payload[:_SNIFF_WINDOW]
    if head.startswith(_PDF) or head.lstrip().startswith(_PDF):
        return SniffResult(kind="pdf", mime="application/pdf", confidence="high")
    if head.startswith(_PNG):
        return SniffResult(kind="png", mime="image/png", confidence="high")
    if head.startswith(_JPEG):
        return SniffResult(kind="jpeg", mime="image/jpeg", confidence="high")
    if head.startswith(_GIF):
        return SniffResult(kind="gif", mime="image/gif", confidence="high")
    if head.startswith(_ZIP) or head.startswith(_ZIP_EMPTY):
        return SniffResult(kind="zip", mime="application/zip", confidence="high")
    if any(head.startswith(marker) for marker in _DWG_MARKERS):
        return SniffResult(kind="dwg", mime="image/vnd.dwg", confidence="high")

    stripped = head.lstrip()
    upper = stripped.upper()
    if any(marker in upper for marker in (m.upper() for m in _IFC_MARKERS)):
        # IFC STEP header may be preceded by comments/BOM within the window.
        return SniffResult(kind="ifc", mime="application/x-step", confidence="high")

    text_prefix = stripped[:200].decode("utf-8", errors="ignore").lstrip().lower()
    if text_prefix.startswith("0\nsection") or text_prefix.startswith("0\r\nsection"):
        return SniffResult(kind="dxf", mime="image/vnd.dxf", confidence="medium")
    if text_prefix.startswith("<?xml") or text_prefix.startswith("<ids"):
        return SniffResult(kind="xml", mime="application/xml", confidence="medium")
    if text_prefix.startswith("{") or text_prefix.startswith("["):
        return SniffResult(kind="json", mime="application/json", confidence="low")

    # Printable text heuristic for .txt/.md/.csv style uploads.
    sample = head[:512]
    if sample and all(32 <= b <= 126 or b in (9, 10, 13) for b in sample):
        return SniffResult(kind="text", mime="text/plain", confidence="low")

    return SniffResult(kind="unknown", mime="application/octet-stream", confidence="low")


# Extension → allowed sniffed kinds (binary formats must match).
_EXTENSION_KINDS: dict[str, frozenset[str]] = {
    ".ifc": frozenset({"ifc"}),
    ".ifczip": frozenset({"zip"}),
    ".pdf": frozenset({"pdf"}),
    ".png": frozenset({"png"}),
    ".jpg": frozenset({"jpeg"}),
    ".jpeg": frozenset({"jpeg"}),
    ".gif": frozenset({"gif"}),
    ".dxf": frozenset({"dxf", "text"}),
    ".dwg": frozenset({"dwg"}),
    ".ids": frozenset({"xml", "text"}),
    ".xml": frozenset({"xml", "text"}),
    ".json": frozenset({"json", "text"}),
    ".txt": frozenset({"text", "json", "xml", "ifc", "dxf"}),
    ".md": frozenset({"text"}),
    ".csv": frozenset({"text"}),
    ".docx": frozenset({"zip"}),
    ".xlsx": frozenset({"zip"}),
    ".pptx": frozenset({"zip"}),
    ".zip": frozenset({"zip"}),
}

# Default allowlist for pilot uploads.
_ALLOWED_EXTENSIONS = frozenset(_EXTENSION_KINDS)

# Closed Autodesk natives: reject with an explicit NOT_IMPLEMENTED reason
# (same class as native DWG). Do not import domain from core.
_AUTODESK_CLOSED_SUFFIXES = frozenset({".rvt", ".rte", ".nwd", ".nwc"})
_AUTODESK_CLOSED_REASON = (
    "native RVT/NWD parser is not implemented; closed Autodesk format without a free reader"
)
_LIRA_CLOSED_SUFFIXES = frozenset({".lir", ".spr"})
NATIVE_LIRA_CLOSED_REASON = (
    "native LIRA parser is not implemented; xlsx/docx table compare is not a solver"
)
_REVIT_CONTAINER_ZIP_BASENAMES = frozenset({"basicfileinfo"})


def extension_of(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1]
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def _zip_names_indicate_autodesk(names: tuple[str, ...]) -> bool:
    for raw in names:
        base = raw.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
        if any(base.endswith(suffix) for suffix in _AUTODESK_CLOSED_SUFFIXES):
            return True
        if base in _REVIT_CONTAINER_ZIP_BASENAMES:
            return True
    return False


def _zip_names_indicate_lira(names: tuple[str, ...]) -> bool:
    for raw in names:
        base = raw.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].lower()
        if any(base.endswith(suffix) for suffix in _LIRA_CLOSED_SUFFIXES):
            return True
    return False


def validate_upload_content(
    *,
    filename: str,
    payload: bytes,
    declared_content_type: str | None = None,
) -> SniffResult:
    """Validate filename extension against sniffed content.

    Raises UploadContentError on empty payload, disallowed extension, or
    extension/magic mismatch for high-confidence binary formats.
    """

    del declared_content_type  # reserved for future MIME cross-check
    if not payload:
        raise UploadContentError("Empty upload")

    ext = extension_of(filename)
    if not ext:
        raise UploadContentError("Upload filename must include an allowed extension")
    if ext in _AUTODESK_CLOSED_SUFFIXES:
        raise UploadContentError(_AUTODESK_CLOSED_REASON)
    if ext in _LIRA_CLOSED_SUFFIXES:
        raise UploadContentError(NATIVE_LIRA_CLOSED_REASON)
    if ext not in _ALLOWED_EXTENSIONS:
        raise UploadContentError(f"Disallowed upload extension: {ext}")

    sniffed = sniff_content(payload)
    allowed = _EXTENSION_KINDS[ext]
    if sniffed.kind == "empty":
        raise UploadContentError("Empty upload")
    if sniffed.kind not in allowed:
        # Soft text formats may sniff as unknown when binary-ish; still reject
        # high-confidence binary mismatches.
        if sniffed.confidence == "high" or sniffed.kind != "unknown":
            raise UploadContentError(
                f"Content mismatch: extension {ext} does not match sniffed type {sniffed.kind}"
            )
        if sniffed.kind == "unknown" and ext in {
            ".ifc",
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".dwg",
            ".ifczip",
            ".docx",
            ".xlsx",
            ".zip",
        }:
            raise UploadContentError(
                f"Content mismatch: extension {ext} does not match sniffed type {sniffed.kind}"
            )
    return sniffed


def reject_autodesk_zip_bytes(payload: bytes) -> None:
    """Reject ZIP members that are closed natives (Autodesk or LIRA).

    Call on the **complete** archive after zip-bomb inspection. Do not run this
    on a sniff-window prefix: the ZIP central directory is at the end of the
    file, so a truncated prefix raises BadZipFile and would mask 422 zip-bomb.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            names = tuple(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise UploadContentError(f"Invalid ZIP archive: {exc}") from exc
    if _zip_names_indicate_autodesk(names):
        raise UploadContentError(_AUTODESK_CLOSED_REASON)
    if _zip_names_indicate_lira(names):
        raise UploadContentError(NATIVE_LIRA_CLOSED_REASON)


def reject_autodesk_zip_path(path: Path) -> None:
    """Path form for the upload quarantine after ``inspect_zip_path``."""

    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = tuple(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise UploadContentError(f"Invalid ZIP archive: {exc}") from exc
    if _zip_names_indicate_autodesk(names):
        raise UploadContentError(_AUTODESK_CLOSED_REASON)
    if _zip_names_indicate_lira(names):
        raise UploadContentError(NATIVE_LIRA_CLOSED_REASON)


__all__ = [
    "SniffResult",
    "UploadContentError",
    "NATIVE_LIRA_CLOSED_REASON",
    "sniff_content",
    "validate_upload_content",
    "reject_autodesk_zip_bytes",
    "reject_autodesk_zip_path",
    "extension_of",
]
