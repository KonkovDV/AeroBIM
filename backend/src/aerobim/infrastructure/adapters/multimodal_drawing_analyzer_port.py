"""DrawingAnalyzerPort facade over MultimodalDrawingPipeline (OCR degrade)."""

from __future__ import annotations

from aerobim.domain.models import DrawingSource
from aerobim.domain.ports import MultimodalDrawingPipeline
from aerobim.domain.tz_architecture_ports import (
    DetectedText,
    DrawingAnalyzerPort,
    SheetType,
    StructuredAnnotations,
)


class MultimodalDrawingAnalyzerPort:
    """TZ DrawingAnalyzerPort — maps multimodal OCR/regions to StructuredAnnotations."""

    def __init__(self, pipeline: MultimodalDrawingPipeline) -> None:
        self._pipeline = pipeline

    def analyze(
        self,
        sheet: DrawingSource,
        sheet_type: SheetType = "unknown",
    ) -> StructuredAnnotations:
        result = self._pipeline.analyze(sheet, mode="auto")
        texts = tuple(
            DetectedText(
                text_id=ann.annotation_id,
                text=ann.observed_value,
                bbox_xyxy=(
                    (
                        float(ann.problem_zone.x or 0.0),
                        float(ann.problem_zone.y or 0.0),
                        float((ann.problem_zone.x or 0.0) + (ann.problem_zone.width or 0.0)),
                        float((ann.problem_zone.y or 0.0) + (ann.problem_zone.height or 0.0)),
                    )
                    if ann.problem_zone is not None
                    else None
                ),
            )
            for ann in result.annotations
        )
        return StructuredAnnotations(
            sheet_id=sheet.sheet_id or (sheet.path.name if sheet.path else "unknown"),
            sheet_type=sheet_type,
            objects=(),
            dimensions=(),
            texts=texts,
            regions=tuple(result.regions),
            pipeline_mode=result.pipeline_mode_used,
            degraded=result.degraded,
            reason=result.reason,
            confidence_floor=0.0,
        )


# Protocol re-export for type checkers / docs
__all__ = ["MultimodalDrawingAnalyzerPort", "DrawingAnalyzerPort"]
