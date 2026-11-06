"""Read PDF page /Rotate and the viewed page frame.

PII priors use the display angle. Character boxes stay in the stored media
box, while the size a viewer uses is after ``/Rotate``. Callers that test a
corner or an off-page glyph take both from here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aerobim.domain.pdf_page_frame import upright_page_size

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
    except Exception:
        return None
    try:
        if not 0 <= page_number < len(document):
            return None
        page = document[page_number]
        raw = int(page.get_rotation())
        rotate = raw % 360
        return rotate if rotate in _ALLOWED else None
    except Exception:
        return None
    finally:
        document.close()


def viewed_pdfium_page(
    page: Any,
) -> tuple[int, tuple[float, float, float, float], float, float]:
    """Return rotation, stored media box, and viewed width and height.

    A missing media box keeps the size PDFium already reports and does not
    turn the boxes a second time.
    """

    rotation = 0
    try:
        rotation = int(page.get_rotation())
    except Exception:
        rotation = 0
    media = None
    try:
        media = page.get_mediabox()
    except Exception:
        media = None
    if media is None:
        width, height = page.get_size()
        box = (0.0, 0.0, float(width), float(height))
        return 0, box, float(width), float(height)
    box = (float(media[0]), float(media[1]), float(media[2]), float(media[3]))
    width, height = upright_page_size(rotation, *box)
    return rotation, box, width, height


__all__ = ["read_page_rotate_degrees", "viewed_pdfium_page"]
