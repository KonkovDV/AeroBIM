"""§3 layer-2 crop adapter: extract ONE region to PNG via isolated pypdfium2.

Implements the ``RegionCropper`` protocol used by ``RegionRestrictedVlmPipeline``.
Coordinate contract matches the former PyMuPDF cropper: ``bbox_xyxy`` is page
points unless ``coordinate_system="normalized-0-1"``.

PDFium runs in a child process (RT-C3PO-002). This module does not import
pypdfium2.
"""

from __future__ import annotations

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.pdfium_isolate.process_isolate import (
    run_pdfium_crop_isolated,
)

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
        png = run_pdfium_crop_isolated(
            {
                "path": str(source.path),
                "page_number": self._page_number,
                "bbox_xyxy": list(bbox_xyxy),
                "dpi": self._dpi,
                "coordinate_system": self._coordinate_system,
                "max_side_px": self._max_side_px,
            }
        )
        return (png, "image/png")


__all__ = ["PdfiumRegionCropper"]
