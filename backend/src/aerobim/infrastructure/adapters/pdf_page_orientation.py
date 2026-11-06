"""Read PDF page /Rotate and the viewed page frame.

PII priors use the display angle. Character boxes stay in the stored media
box, while the size a viewer uses is after ``/Rotate``. Callers that test a
corner or an off-page glyph take both from here.
"""

from __future__ import annotations

import ctypes
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from aerobim.domain.pdf_page_frame import media_box_from_viewed_size, upright_page_size

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

    A missing media box is rebuilt from the viewed size and the rotation,
    with the origin at zero. The boxes are still turned once.
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
        box = media_box_from_viewed_size(rotation, float(width), float(height))
        viewed_w, viewed_h = upright_page_size(rotation, *box)
        return rotation, box, viewed_w, viewed_h
    box = (float(media[0]), float(media[1]), float(media[2]), float(media[3]))
    width, height = upright_page_size(rotation, *box)
    return rotation, box, width, height


def iter_pdfium_chars(
    textpage: Any,
) -> Iterator[tuple[int, str, float, float, float, float]]:
    """Yield each character and its stored box.

    ``FPDFText_GetUnicode`` is the code point PDFium indexes for the box.
    One box buffer is reused for the whole page. A code point of 0 is an
    empty slot and still yields a box. A failed box raises, as
    ``get_charbox`` does. This is the PDFium walk, not a second parser.
    """

    import pypdfium2.raw as pdfium_c
    from pypdfium2._helpers.misc import PdfiumError

    raw = textpage.raw
    get_unicode = pdfium_c.FPDFText_GetUnicode
    get_box = pdfium_c.FPDFText_GetCharBox
    left_b = ctypes.c_double()
    right_b = ctypes.c_double()
    bottom_b = ctypes.c_double()
    top_b = ctypes.c_double()
    count = int(textpage.count_chars())
    for index in range(count):
        code = int(get_unicode(raw, index))
        char = chr(code) if code else ""
        if not get_box(raw, index, left_b, right_b, bottom_b, top_b):
            raise PdfiumError("Failed to get charbox.")
        yield (
            index,
            char,
            left_b.value,
            bottom_b.value,
            right_b.value,
            top_b.value,
        )


__all__ = ["iter_pdfium_chars", "read_page_rotate_degrees", "viewed_pdfium_page"]
