"""Heuristic sheet layout region detector (Blueprint-aligned priors, no YOLO weights)."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import DrawingRegionRef


class HeuristicLayoutRegionDetector:
    """Emit normalized layout regions for title block / stamp / content.

    Advisory only — low confidence, modality ``detector``. Does **not** claim
    human-level CV; ``cv_human_level`` must stay MISSING until labeled corpus F1.
    """

    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]:
        if not path.is_file():
            return []
        sid = (sheet_id or path.stem).upper()
        # Normalized sheet coordinates (0..1): content band, title block, stamp.
        return [
            DrawingRegionRef(
                sheet_id=sid,
                bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
                confidence=0.35,
                modality="detector",
            ),
            DrawingRegionRef(
                sheet_id=sid,
                bbox_xyxy=(0.55, 0.85, 1.0, 1.0),
                confidence=0.4,
                modality="detector",
            ),
            DrawingRegionRef(
                sheet_id=sid,
                bbox_xyxy=(0.0, 0.85, 0.25, 1.0),
                confidence=0.3,
                modality="detector",
            ),
        ]
