"""Read the viewed frame of a PDFium page.

Character boxes stay in the stored media box. The size a viewer uses is
after ``/Rotate``. Callers that test a corner or an off-page glyph need
both from one place.
"""

from __future__ import annotations

from typing import Any

from aerobim.domain.pdf_page_frame import upright_page_size


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


__all__ = ["viewed_pdfium_page"]
