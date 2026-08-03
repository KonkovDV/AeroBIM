"""Read PDF page /Rotate for PII prior orientation (RT-STAMP-14)."""

from __future__ import annotations

from pathlib import Path

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
_ALLOWED = frozenset({0, 90, 180, 270})


def read_page_rotate_degrees(path: Path, *, page_number: int = 0) -> int | None:
    """Return page display rotation in degrees, or None if unknown/unsupported.

    Raster images are treated as already visual (0). PDFs use pypdfium2
    ``get_rotation``. Any other value or I/O failure → ``None`` (caller
    fail-closes the PII guard).
    """
    suffix = path.suffix.lower()
    if suffix in _IMAGE_SUFFIXES:
        return 0
    if suffix != ".pdf":
        return None
    try:
        import pypdfium2 as pdfium
    except ModuleNotFoundError:
        return None
    try:
        document = pdfium.PdfDocument(str(path))
    except Exception:  # noqa: BLE001 — orientation probe must never raise into VLM
        return None
    try:
        if not 0 <= page_number < len(document):
            return None
        page = document[page_number]
        raw = int(page.get_rotation())
        rotate = raw % 360
        return rotate if rotate in _ALLOWED else None
    except Exception:  # noqa: BLE001
        return None
    finally:
        document.close()


__all__ = ["read_page_rotate_degrees"]
