"""Heuristic sheet layout region detector (Blueprint-aligned priors, no YOLO weights)."""

from __future__ import annotations

from pathlib import Path

from aerobim.domain.models import DrawingRegionRef

# Confidence below this mark forces HITL (advisory detector, not CV_VERIFIED).
_HITL_CONFIDENCE = 0.45


class HeuristicLayoutRegionDetector:
    """Emit normalized layout regions for title block / stamp / content / tables.

    Advisory only — low confidence, modality ``detector``. Does **not** claim
    human-level CV; ``cv_human_level`` must stay MISSING until labeled corpus F1.

    ``layout_role=stamp`` marks the lower-right prior so cloud VLM can exclude it
    (signatory PII → RESTRICTED without DPA / C2).

    Status for roadmap P1.1: ``HEURISTIC_BASELINE``, not ``CV_VERIFIED``.
    """

    def detect(self, path: Path, *, sheet_id: str | None = None) -> list[DrawingRegionRef]:
        if not path.is_file():
            return []
        sid = (sheet_id or path.stem).upper()
        # Normalized sheet coordinates (0..1): Blueprint-style priors.
        priors: list[tuple[tuple[float, float, float, float], float, str, str | None]] = [
            # (bbox_xyxy, confidence, layout_role, hitl_reason)
            ((0.0, 0.0, 1.0, 0.78), 0.35, "content", "low_confidence<0.45"),
            ((0.55, 0.82, 1.0, 1.0), 0.4, "stamp", "low_confidence<0.45"),
            ((0.0, 0.82, 0.28, 1.0), 0.3, "title_block", "low_confidence<0.45"),
            # Spec / schedule band — mid-right table prior (not trained CV).
            ((0.62, 0.35, 1.0, 0.78), 0.28, "specification", "heuristic_spec_band"),
            # Dimension chain band — lower content strip (not trained CV).
            ((0.05, 0.68, 0.55, 0.82), 0.28, "dimension_chain", "heuristic_dim_band"),
        ]
        regions: list[DrawingRegionRef] = []
        for bbox, confidence, role, reason in priors:
            hitl = confidence < _HITL_CONFIDENCE
            regions.append(
                DrawingRegionRef(
                    sheet_id=sid,
                    bbox_xyxy=bbox,
                    confidence=confidence,
                    modality="detector",
                    layout_role=role,
                    hitl_required=hitl,
                    hitl_reason=reason if hitl else None,
                    coordinate_system="normalized-0-1",
                )
            )
        return regions


__all__ = ["HeuristicLayoutRegionDetector"]
