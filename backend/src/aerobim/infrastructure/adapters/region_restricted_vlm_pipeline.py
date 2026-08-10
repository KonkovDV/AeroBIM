"""§3 layer 2: region-restricted VLM orchestration (advisory, fail-closed).

Composes a layout detector (layer 1) + a deterministic read plan (layers 0-1) +
a region cropper + the advisory reader, so the VLM only ever sees ONE region
crop at a time (never the whole sheet). Every outcome is ``degraded=True`` —
these are candidate observations, not findings; the verdict stays with the
deterministic engine and the expert (ADR-001).

Fail-closed everywhere: not ready, no cropper, no path, text layer present, no
regions, a per-region crop/read/parse failure — each degrades without inventing
observations and without a whole-sheet read.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from aerobim.domain.models import DrawingRegionRef, DrawingSource
from aerobim.domain.region_read_plan import RegionReadTask, plan_region_reads
from aerobim.domain.vlm_grounding import VlmObservation, ground_vlm_region_observations
from aerobim.infrastructure.adapters.vlm_advisory_client import (
    VlmAdvisoryError,
    VlmReadResult,
)
from aerobim.infrastructure.adapters.pdf_page_orientation import read_page_rotate_degrees

_DEFAULT_MAX_REGIONS = 24
_DEFAULT_REGION_PROMPT = (
    "You are reading ONE cropped region of an engineering drawing. Extract only "
    "text physically visible in this crop (title-block fields, marks, dimensions, "
    "table rows). Do not infer, do not count, do not judge compliance. Return JSON "
    "per the schema; if the crop is unreadable, set readable=false with a reason."
)


class _RegionReader(Protocol):
    def read_region(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, region_id: str, prompt: str
    ) -> VlmReadResult: ...


class _RegionDetector(Protocol):
    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]: ...


class RegionCropper(Protocol):
    """Crops one region to raw image bytes; returns ``(bytes, media_type)``."""

    def crop(
        self, source: DrawingSource, *, bbox_xyxy: tuple[float, float, float, float]
    ) -> tuple[bytes, str]: ...


@dataclass(frozen=True)
class RegionRead:
    region_id: str
    observations: tuple[VlmObservation, ...]
    degraded: bool
    reason: str | None
    determinism_basis: str = "unavailable"
    crop_sha256: str = ""
    control_fields_ignored: tuple[str, ...] = ()
    dropped_count: int = 0


@dataclass(frozen=True)
class SheetReadResult:
    sheet_id: str
    skipped_vlm: bool
    reason: str
    reads: tuple[RegionRead, ...] = ()
    degraded: bool = True  # candidates only; cv_human_level remains MISSING
    regions_detected: int = 0
    regions_planned: int = 0
    regions_read: int = 0
    regions_truncated: int = 0
    truncation_reason: str | None = None
    region_plan_sha256: str = ""
    stamp_regions_excluded: int = 0
    excluded_by_role: int = 0
    excluded_by_crs: int = 0
    excluded_by_pii_clip: int = 0
    excluded_by_geometry: int = 0
    excluded_unknown_role: int = 0
    page_rotate_degrees: int | None = None


def _region_plan_sha256(tasks: tuple[RegionReadTask, ...]) -> str:
    payload = ";".join(
        f"{task.region_id}:{task.coordinate_system}:{task.bbox_xyxy}:{task.layout_role or ''}"
        for task in tasks
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RegionRestrictedVlmPipeline:
    """Layer-0/1/2 advisory orchestrator; the whole sheet is never sent to the VLM."""

    def __init__(
        self,
        *,
        region_detector: _RegionDetector | None,
        reader: _RegionReader | None,
        cropper: RegionCropper | None,
        ready: bool,
        min_confidence: float = 0.60,
        max_regions: int = _DEFAULT_MAX_REGIONS,
        prompt: str = _DEFAULT_REGION_PROMPT,
        exclude_stamp_regions: bool = True,
    ) -> None:
        if ready and not exclude_stamp_regions:
            raise ValueError(
                "PII guard (exclude_stamp_regions) cannot be disabled when the "
                "region-restricted VLM pipeline is ready"
            )
        self._region_detector = region_detector
        self._reader = reader
        self._cropper = cropper
        self._ready = ready
        self._min_confidence = min_confidence
        self._max_regions = max_regions
        self._prompt = prompt
        self._exclude_stamp_regions = exclude_stamp_regions

    @property
    def ready(self) -> bool:
        """True only when a reader, cropper and detector are wired (advisory available)."""
        return (
            self._ready
            and self._reader is not None
            and self._cropper is not None
            and self._region_detector is not None
        )

    def read_sheet(self, source: DrawingSource, *, text_layer_present: bool) -> SheetReadResult:
        sheet_id = source.sheet_id or (source.path.stem if source.path else "sheet")
        # Fail-closed: without reader/cropper/detector/path we do NOT read the
        # whole sheet — region-restricted is the only permitted VLM path.
        if (
            not self._ready
            or self._reader is None
            or self._cropper is None
            or self._region_detector is None
            or source.path is None
        ):
            return SheetReadResult(
                sheet_id=sheet_id,
                skipped_vlm=True,
                reason="region-restricted VLM unavailable (not ready / no cropper); "
                "whole-sheet read is forbidden",
            )

        regions = self._region_detector.detect(source.path, sheet_id=source.sheet_id)
        page_rotate = read_page_rotate_degrees(source.path) if self._exclude_stamp_regions else 0
        plan = plan_region_reads(
            text_layer_present=text_layer_present,
            regions=regions,
            exclude_stamp_regions=self._exclude_stamp_regions,
            page_rotate_degrees=page_rotate,
        )
        detected = len(regions)
        if plan.skip_vlm:
            return SheetReadResult(
                sheet_id=sheet_id,
                skipped_vlm=True,
                reason=plan.reason,
                regions_detected=detected,
                stamp_regions_excluded=plan.stamp_regions_excluded,
                excluded_by_role=plan.excluded_by_role,
                excluded_by_crs=plan.excluded_by_crs,
                excluded_by_pii_clip=plan.excluded_by_pii_clip,
                excluded_by_geometry=plan.excluded_by_geometry,
                excluded_unknown_role=plan.excluded_unknown_role,
                page_rotate_degrees=page_rotate,
            )

        planned = len(plan.tasks)
        selected = plan.tasks[: self._max_regions]
        truncated = planned - len(selected)
        reads = tuple(self._read_one(source, sheet_id, task) for task in selected)
        return SheetReadResult(
            sheet_id=sheet_id,
            skipped_vlm=False,
            reason=plan.reason,
            reads=reads,
            regions_detected=detected,
            regions_planned=planned,
            regions_read=len(selected),
            regions_truncated=truncated,
            truncation_reason=(
                f"max_regions={self._max_regions} budget: {truncated} region(s) not read"
                if truncated
                else None
            ),
            region_plan_sha256=_region_plan_sha256(plan.tasks),
            stamp_regions_excluded=plan.stamp_regions_excluded,
            excluded_by_role=plan.excluded_by_role,
            excluded_by_crs=plan.excluded_by_crs,
            excluded_by_pii_clip=plan.excluded_by_pii_clip,
            excluded_by_geometry=plan.excluded_by_geometry,
            excluded_unknown_role=plan.excluded_unknown_role,
            page_rotate_degrees=page_rotate,
        )

    def _read_one(self, source: DrawingSource, sheet_id: str, task: RegionReadTask) -> RegionRead:
        assert self._cropper is not None and self._reader is not None  # narrowed by caller
        crop_sha = ""
        try:
            if self._exclude_stamp_regions and task.coordinate_system != "normalized-0-1":
                return RegionRead(
                    task.region_id,
                    (),
                    True,
                    "PII guard requires normalized-0-1 task CRS; refuse crop",
                )
            crop_bytes, media_type = self._cropper.crop(source, bbox_xyxy=task.bbox_xyxy)
            crop_sha = hashlib.sha256(crop_bytes).hexdigest()
            read = self._reader.read_region(
                crop_bytes,
                media_type=media_type,
                sheet_id=sheet_id,
                region_id=task.region_id,
                prompt=self._prompt,
            )
        except VlmAdvisoryError as exc:
            return RegionRead(
                task.region_id, (), True, f"read failed ({exc.reason_code})", crop_sha256=crop_sha
            )
        except (OSError, ValueError) as exc:
            return RegionRead(
                task.region_id, (), True, f"crop/read failed: {exc}", crop_sha256=crop_sha
            )
        except Exception as exc:  # noqa: BLE001 — transport/SSRF must fail closed
            return RegionRead(
                task.region_id,
                (),
                True,
                f"transport error (fail-closed): {exc}",
                crop_sha256=crop_sha,
            )

        grounded = ground_vlm_region_observations(
            read.content,
            sheet_id=sheet_id,
            region_id=task.region_id,
            min_confidence=self._min_confidence,
        )
        if not grounded.parse_ok:
            return RegionRead(
                task.region_id,
                (),
                True,
                f"schema deviation: {grounded.reason}",
                crop_sha256=crop_sha,
                control_fields_ignored=grounded.control_fields_ignored,
                dropped_count=grounded.dropped_count,
            )
        return RegionRead(
            task.region_id,
            grounded.observations,
            True,
            grounded.reason,
            read.determinism_basis,
            crop_sha,
            grounded.control_fields_ignored,
            grounded.dropped_count,
        )


__all__ = ["RegionCropper", "RegionRead", "RegionRestrictedVlmPipeline", "SheetReadResult"]
