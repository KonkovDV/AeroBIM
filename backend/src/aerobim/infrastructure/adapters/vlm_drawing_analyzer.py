"""VLM-based drawing analyzer adapter.

/** @sota-stub */

Planned adapter for extracting semantic annotations from raster/PDF
drawings using Vision Language Models (Qwen-VL, Florence-2, etc.).

Currently returns an empty list — production implementation will add:
  - PDF → image rasterization (pdf2image / PyMuPDF)
  - ONNX Runtime inference with int8 quantised VLM
  - Bounding-box → DrawingAnnotation mapping
  - Confidence filtering

Tracked in: docs/04-atomic-backlog.md — VLM Drawing Analyzer item.
"""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import DrawingAnnotation


class VlmDrawingAnalyzer:
    """Infrastructure adapter implementing ``VisionDrawingAnalyzer`` port.

    /** @sota-stub */
    """

    def analyze_image(
        self,
        image_path: Path,
        sheet_id: str | None = None,
    ) -> list[DrawingAnnotation]:
        if not image_path.exists():
            raise FileNotFoundError(f"Drawing image not found: {image_path}")
        # Stub: real implementation will run VLM inference here.
        return []
