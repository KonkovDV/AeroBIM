"""Map a stored PDF character box onto the upright page.

``/Rotate`` is how the sheet is shown. A PDFium character box stays in the
stored user space, while the page width and height are the viewed sheet.
A title-block corner and an off-page test are about that viewed sheet.
The turn is the same one pdfminer applies before it places a character.
This does not write ``summary.passed``.
"""

from __future__ import annotations

_QUARTER_TURNS = frozenset({0, 90, 180, 270})


def normalize_page_rotation(rotation: int) -> int:
    """Return 0, 90, 180 or 270. Any other angle is left unturned."""

    turned = int(rotation) % 360
    if turned in _QUARTER_TURNS:
        return turned
    return 0


def upright_page_size(
    rotation: int,
    media_x0: float,
    media_y0: float,
    media_x1: float,
    media_y1: float,
) -> tuple[float, float]:
    """Viewed width and height. A quarter turn swaps the stored sides."""

    width = abs(media_x1 - media_x0)
    height = abs(media_y1 - media_y0)
    if normalize_page_rotation(rotation) in (90, 270):
        return height, width
    return width, height


def upright_char_box(
    left: float,
    bottom: float,
    right: float,
    top: float,
    *,
    rotation: int,
    media_x0: float,
    media_y0: float,
    media_x1: float,
    media_y1: float,
) -> tuple[float, float, float, float]:
    """Return the box in upright bottom-left coordinates, origin at the corner.

    The four corners are turned and then enclosed. A stored box that is not
    axis-aligned after the turn still yields an axis-aligned bound.
    """

    turned = normalize_page_rotation(rotation)
    corners = (
        (left, bottom),
        (right, bottom),
        (left, top),
        (right, top),
    )
    mapped = [
        _upright_point(
            x,
            y,
            rotation=turned,
            media_x0=media_x0,
            media_y0=media_y0,
            media_x1=media_x1,
            media_y1=media_y1,
        )
        for x, y in corners
    ]
    xs = [point[0] for point in mapped]
    ys = [point[1] for point in mapped]
    return (min(xs), min(ys), max(xs), max(ys))


def _upright_point(
    x: float,
    y: float,
    *,
    rotation: int,
    media_x0: float,
    media_y0: float,
    media_x1: float,
    media_y1: float,
) -> tuple[float, float]:
    if rotation == 90:
        return (y - media_y0, media_x1 - x)
    if rotation == 180:
        return (media_x1 - x, media_y1 - y)
    if rotation == 270:
        return (media_y1 - y, x - media_x0)
    return (x - media_x0, y - media_y0)


def writes_summary_passed() -> bool:
    return False


__all__ = [
    "normalize_page_rotation",
    "upright_char_box",
    "upright_page_size",
    "writes_summary_passed",
]
