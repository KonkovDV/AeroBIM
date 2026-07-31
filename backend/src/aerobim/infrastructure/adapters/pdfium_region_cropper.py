"""§3 layer-2 crop adapter: extract ONE region to PNG via pypdfium2 (LIC-001 Option B).

Implements the ``RegionCropper`` protocol used by ``RegionRestrictedVlmPipeline``.
Coordinate contract matches the former PyMuPDF cropper: ``bbox_xyxy`` is page
points unless ``coordinate_system="normalized-0-1"``.
"""

from __future__ import annotations

import io

from aerobim.domain.models import DrawingSource

_DEFAULT_DPI = 200
_DEFAULT_MAX_SIDE_PX = 4096


class PdfiumRegionCropper:
    """Crops one region of a PDF page to PNG bytes (permissive PDFium path)."""

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
            import pypdfium2 as pdfium
        except ModuleNotFoundError as exc:  # pragma: no cover - core dep
            raise RuntimeError("Region cropping requires pypdfium2 (core PDF backend)") from exc
        try:
            from PIL import Image
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("Region cropping requires Pillow (core dependency)") from exc

        document = pdfium.PdfDocument(str(source.path))
        try:
            if not 0 <= self._page_number < len(document):
                raise ValueError(f"page {self._page_number} out of range (pages={len(document)})")
            page = document[self._page_number]
            width_pt = float(page.get_width())
            height_pt = float(page.get_height())
            x1, y1, x2, y2 = self._normalize_bbox(bbox_xyxy, width_pt, height_pt)
            # Intersect with page; PDF y-axis origin is bottom-left for render crop.
            left = max(0.0, min(x1, x2))
            right = min(width_pt, max(x1, x2))
            top_from_top = max(0.0, min(y1, y2))
            bottom_from_top = min(height_pt, max(y1, y2))
            if right - left <= 0 or bottom_from_top - top_from_top <= 0:
                raise ValueError(f"degenerate/out-of-bounds crop rect for bbox={bbox_xyxy}")

            dpi = self._bounded_dpi(right - left, bottom_from_top - top_from_top)
            scale = dpi / 72.0
            # pypdfium2 crop = amount cut from (left, bottom, right, top) edges.
            cut_left = left
            cut_right = width_pt - right
            cut_top = top_from_top
            cut_bottom = height_pt - bottom_from_top
            bitmap = page.render(
                scale=scale,
                crop=(cut_left, cut_bottom, cut_right, cut_top),
            )
            image = bitmap.to_pil()
            if not isinstance(image, Image.Image):
                raise RuntimeError("pypdfium2 render did not yield a PIL image")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return (buffer.getvalue(), "image/png")
        finally:
            document.close()

    def _normalize_bbox(
        self,
        bbox: tuple[float, float, float, float],
        width_pt: float,
        height_pt: float,
    ) -> tuple[float, float, float, float]:
        x1, y1, x2, y2 = bbox
        if self._coordinate_system == "normalized-0-1":
            x1, x2 = x1 * width_pt, x2 * width_pt
            y1, y2 = y1 * height_pt, y2 * height_pt
        return x1, y1, x2, y2

    def _bounded_dpi(self, width_pt: float, height_pt: float) -> int:
        longest_pt = max(width_pt, height_pt)
        if longest_pt <= 0:
            return self._dpi
        max_dpi_for_budget = int(self._max_side_px * 72 / longest_pt)
        return max(72, min(self._dpi, max_dpi_for_budget))


__all__ = ["PdfiumRegionCropper"]
