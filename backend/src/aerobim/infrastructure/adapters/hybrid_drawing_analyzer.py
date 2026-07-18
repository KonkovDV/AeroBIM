"""HybridDrawingAnalyzer — allowlisted sheet detector+VLM with OCR degrade.

Vision extra (``aerobim-backend[vision]``) enables Pillow-backed priors only.
No YOLO weights ship; modality remains ``detector`` priors / future YOLO.
``cv_human_level`` never becomes OK (AECV-Bench symbol counting unsolved 0.40–0.55).
"""

from __future__ import annotations

from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.domain.ports import DrawingRegionDetector, RasterDrawingAnalyzer
from aerobim.domain.tz_architecture_ports import (
    DetectedObject,
    DetectedText,
    SheetType,
    StructuredAnnotations,
)

_ALLOWLIST: frozenset[SheetType] = frozenset({"plan_ar", "plan_ov", "title_block"})


def _vision_available() -> bool:
    try:
        import PIL  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


class HybridDrawingAnalyzer:
    """Detector priors + OCR degrade; VLM path is advisory / stub without weights.

    Rationale: Khan RCIM narrow-domain high scores ≠ product; AECV-Bench shows
    symbol counting remains unsolved — CV stays advisory + HITL (I8c).
    """

    def __init__(
        self,
        *,
        raster_analyzer: RasterDrawingAnalyzer | None = None,
        region_detector: DrawingRegionDetector | None = None,
        allowlist: frozenset[SheetType] | None = None,
        confidence_floor: float = 0.45,
    ) -> None:
        self._raster = raster_analyzer
        self._region_detector = region_detector
        self._allowlist = allowlist or _ALLOWLIST
        self._confidence_floor = confidence_floor

    def analyze(
        self,
        sheet: DrawingSource,
        sheet_type: SheetType = "unknown",
    ) -> StructuredAnnotations:
        sheet_id = sheet.sheet_id or (sheet.path.name if sheet.path else "unknown")

        # Allowlist gate first: outside-allowlist degrade must not depend on vision extra.
        if sheet_type not in self._allowlist:
            return self._ocr_degrade(
                sheet,
                sheet_id=sheet_id,
                sheet_type=sheet_type,
                reason=(
                    f"sheet_type={sheet_type!r} outside hybrid allowlist "
                    f"{sorted(self._allowlist)}; OCR-only"
                ),
                pipeline_mode="ocr_degrade_outside_allowlist",
            )

        if not _vision_available():
            return self._ocr_degrade(
                sheet,
                sheet_id=sheet_id,
                sheet_type=sheet_type,
                reason=(
                    "vision optional extra not installed "
                    "(pip install aerobim-backend[vision]); OCR degrade"
                ),
                pipeline_mode="ocr_degrade_no_vision",
            )

        regions: list[DrawingRegionRef] = []
        if sheet.path is not None and self._region_detector is not None:
            regions.extend(self._region_detector.detect(sheet.path, sheet_id=sheet.sheet_id))

        # Future YOLO / VLM slot: without weights emit low-confidence prior object.
        objects = (
            DetectedObject(
                object_id=f"prior-{sheet_id}-layout",
                kind="layout_prior",
                bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
                confidence=0.35,
            ),
        )
        # Mark detector regions for HITL when below floor (I8c path consumes hitl_required).
        hitl_regions: list[DrawingRegionRef] = []
        for region in regions:
            if region.confidence < self._confidence_floor:
                from dataclasses import replace

                hitl_regions.append(
                    replace(
                        region,
                        hitl_required=True,
                        hitl_reason=f"hybrid_low_confidence<{self._confidence_floor}",
                    )
                )
            else:
                hitl_regions.append(region)

        texts = self._ocr_texts(sheet)
        return StructuredAnnotations(
            sheet_id=sheet_id,
            sheet_type=sheet_type,
            objects=objects,
            dimensions=(),
            texts=texts,
            regions=tuple(hitl_regions),
            pipeline_mode="hybrid_priors_ocr",
            degraded=True,
            reason=(
                "Hybrid detector priors + OCR (no YOLO weights; future YOLO behind same port); "
                "cv_human_level remains MISSING — AECV-Bench symbol counting unsolved"
            ),
            confidence_floor=self._confidence_floor,
        )

    def _ocr_degrade(
        self,
        sheet: DrawingSource,
        *,
        sheet_id: str,
        sheet_type: SheetType,
        reason: str,
        pipeline_mode: str,
    ) -> StructuredAnnotations:
        texts = self._ocr_texts(sheet)
        regions: tuple[DrawingRegionRef, ...] = ()
        if sheet.path is not None and self._region_detector is not None:
            regions = tuple(self._region_detector.detect(sheet.path, sheet_id=sheet.sheet_id))
        return StructuredAnnotations(
            sheet_id=sheet_id,
            sheet_type=sheet_type,
            objects=(),
            dimensions=(),
            texts=texts,
            regions=regions,
            pipeline_mode=pipeline_mode,
            degraded=True,
            reason=reason,
            confidence_floor=self._confidence_floor,
        )

    def _ocr_texts(self, sheet: DrawingSource) -> tuple[DetectedText, ...]:
        if self._raster is None or sheet.path is None:
            return ()
        try:
            annotations = self._raster.analyze_image(sheet.path, sheet_id=sheet.sheet_id)
        except Exception:  # noqa: BLE001
            return ()
        return tuple(
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
            for ann in annotations
        )
