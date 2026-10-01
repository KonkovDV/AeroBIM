"""§3 layer-2 crop adapter: extract ONE region to PNG bytes via PyMuPDF.

Optional AGPL path (``pdf-agpl`` extra / ``AEROBIM_PDF_BACKEND=pymupdf``).
Production default is ``PdfiumRegionCropper`` (LIC-001 Option B).
"""

from __future__ import annotations

from typing import Any

from aerobim.domain.models import DrawingSource

_DEFAULT_DPI = 200
_DEFAULT_MAX_SIDE_PX = 4096


class PyMuPDFRegionCropper:
    """Crops one region of a PDF page / raster image to PNG bytes."""

    def __init__(
        self,
        *,
        dpi: int = _DEFAULT_DPI,
        page_number: int = 0,
        coordinate_system: str = "page-point",
        max_side_px: int = _DEFAULT_MAX_SIDE_PX,
    ) -> None:
        self._dpi = dpi
        self._page_number = page_number
        self._coordinate_system = coordinate_system
        self._max_side_px = max_side_px

    def crop(
        self, source: DrawingSource, *, bbox_xyxy: tuple[float, float, float, float]
    ) -> tuple[bytes, str]:
        if source.path is None:
            raise ValueError("cannot crop: DrawingSource has no path")
        try:
            import pymupdf
        except ModuleNotFoundError as exc:  # pragma: no cover - shipped core dep
            raise RuntimeError(
                "Region cropping requires PyMuPDF. Install the optional 'pdf-agpl' extra."
            ) from exc

        with pymupdf.open(source.path) as document:
            if not 0 <= self._page_number < document.page_count:
                raise ValueError(
                    f"page {self._page_number} out of range (pages={document.page_count})"
                )
            page = document[self._page_number]
            rect = self._clip_rect(pymupdf, page.rect, bbox_xyxy)
            dpi = self._bounded_dpi(rect)
            pixmap = page.get_pixmap(clip=rect, dpi=dpi)
            return (pixmap.tobytes("png"), "image/png")

    def _clip_rect(
        self,
        pymupdf: Any,
        page_rect: Any,
        bbox: tuple[float, float, float, float],
    ) -> Any:
        x1, y1, x2, y2 = bbox
        if self._coordinate_system == "page-point" and max(bbox) <= 1.0 and min(bbox) >= 0.0:
            raise ValueError(
                "bbox looks normalized-0-1 but cropper coordinate_system is page-point; "
                "refuse ambiguous crop (set coordinate_system='normalized-0-1')"
            )
        if self._coordinate_system == "normalized-0-1":
            x1, x2 = x1 * page_rect.width, x2 * page_rect.width
            y1, y2 = y1 * page_rect.height, y2 * page_rect.height
        # Intersect with the page to clamp defensively, then reject empties.
        rect = pymupdf.Rect(x1, y1, x2, y2) & page_rect
        if rect.is_empty or rect.width <= 0 or rect.height <= 0:
            raise ValueError(f"degenerate/out-of-bounds crop rect for bbox={bbox}")
        return rect

    def _bounded_dpi(self, rect: Any) -> int:
        """Cap the effective dpi so the longest rendered side stays within budget."""
        longest_pt = max(rect.width, rect.height)
        if longest_pt <= 0:
            return self._dpi
        max_dpi_for_budget = int(self._max_side_px * 72 / longest_pt)
        return max(72, min(self._dpi, max_dpi_for_budget))


__all__ = ["PyMuPDFRegionCropper"]
