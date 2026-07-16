"""Multimodal drawing pipeline with mandatory OCR degrade (no fake VLM OK)."""

from __future__ import annotations

from typing import Literal

from aerobim.domain.consistency import MultimodalDrawingResult
from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.domain.ports import RasterDrawingAnalyzer


class OcrFallbackMultimodalDrawingPipeline:
    """Detector+VLM not shipped — always degrade to RasterDrawingAnalyzer when available.

    Honesty: ``cv_human_level`` must remain MISSING; this adapter never implies VLM delivery.
    """

    def __init__(self, raster_analyzer: RasterDrawingAnalyzer | None = None) -> None:
        self._raster = raster_analyzer

    def analyze(
        self,
        source: DrawingSource,
        *,
        mode: Literal["auto", "ocr_only", "detector_vlm"] = "auto",
    ) -> MultimodalDrawingResult:
        if mode == "detector_vlm":
            # Explicit request still degrades — extras not productized.
            pass

        if source.path is None:
            return MultimodalDrawingResult(
                annotations=(),
                regions=(),
                pipeline_mode_used="none",
                degraded=True,
                reason="Multimodal pipeline requires a drawing file path",
            )

        if self._raster is None:
            return MultimodalDrawingResult(
                annotations=(),
                regions=(),
                pipeline_mode_used="unavailable",
                degraded=True,
                reason="RasterDrawingAnalyzer not configured; detector/VLM extras not installed",
            )

        annotations = tuple(self._raster.analyze_image(source.path, sheet_id=source.sheet_id))
        regions = tuple(
            DrawingRegionRef(
                sheet_id=ann.sheet_id,
                bbox_xyxy=(
                    float(ann.problem_zone.x or 0.0),
                    float(ann.problem_zone.y or 0.0),
                    float((ann.problem_zone.x or 0.0) + (ann.problem_zone.width or 0.0)),
                    float((ann.problem_zone.y or 0.0) + (ann.problem_zone.height or 0.0)),
                ),
                confidence=0.5,
                modality="ocr",
            )
            for ann in annotations
            if ann.problem_zone is not None
        )
        return MultimodalDrawingResult(
            annotations=annotations,
            regions=regions,
            pipeline_mode_used="ocr_only",
            degraded=True,
            reason=(
                "Degraded to OCR (RapidOCR path); detector+VLM extras not installed — "
                "cv_human_level remains MISSING"
            ),
        )
