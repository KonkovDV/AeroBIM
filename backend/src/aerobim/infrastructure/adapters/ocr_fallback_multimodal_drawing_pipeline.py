"""Multimodal drawing pipeline with mandatory OCR degrade (no fake VLM OK)."""

from __future__ import annotations

from typing import Literal

from aerobim.domain.consistency import MultimodalDrawingResult
from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.domain.ports import DrawingRegionDetector, RasterDrawingAnalyzer


class OcrFallbackMultimodalDrawingPipeline:
    """Detector priors + OCR degrade — never implies VLM / cv_human_level delivery.

    I8a: optional ``DrawingRegionDetector`` supplies Blueprint-style layout regions;
    OCR annotations still produce ``modality=ocr`` regions. Full-page VLM not shipped.
    """

    def __init__(
        self,
        raster_analyzer: RasterDrawingAnalyzer | None = None,
        region_detector: DrawingRegionDetector | None = None,
    ) -> None:
        self._raster = raster_analyzer
        self._region_detector = region_detector

    def analyze(
        self,
        source: DrawingSource,
        *,
        mode: Literal["auto", "ocr_only", "detector_vlm"] = "auto",
    ) -> MultimodalDrawingResult:
        if mode == "detector_vlm":
            # Explicit request still degrades — VLM extras not productized.
            pass

        if source.path is None:
            return MultimodalDrawingResult(
                annotations=(),
                regions=(),
                pipeline_mode_used="none",
                degraded=True,
                reason="Multimodal pipeline requires a drawing file path",
            )

        detector_regions: tuple[DrawingRegionRef, ...] = ()
        if mode != "ocr_only" and self._region_detector is not None:
            detector_regions = tuple(
                self._region_detector.detect(source.path, sheet_id=source.sheet_id)
            )

        if self._raster is None:
            if detector_regions:
                return MultimodalDrawingResult(
                    annotations=(),
                    regions=detector_regions,
                    pipeline_mode_used="detector_only",
                    degraded=True,
                    reason=(
                        "Layout detector priors only; RasterDrawingAnalyzer absent — "
                        "cv_human_level remains MISSING"
                    ),
                )
            return MultimodalDrawingResult(
                annotations=(),
                regions=(),
                pipeline_mode_used="unavailable",
                degraded=True,
                reason="RasterDrawingAnalyzer not configured; detector/VLM extras not installed",
            )

        annotations = tuple(self._raster.analyze_image(source.path, sheet_id=source.sheet_id))
        ocr_regions = tuple(
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
        regions = tuple([*detector_regions, *ocr_regions])
        pipeline_mode = "detector+ocr" if detector_regions else "ocr_only"
        return MultimodalDrawingResult(
            annotations=annotations,
            regions=regions,
            pipeline_mode_used=pipeline_mode,
            degraded=True,
            reason=(
                "Degraded multimodal path (heuristic detector priors + OCR); "
                "VLM extras not installed — cv_human_level remains MISSING"
            ),
        )
