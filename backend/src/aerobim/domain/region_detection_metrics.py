"""Region detection metrics (P1.2) — IoU@threshold P/R, never product CV accuracy.

Uses ``intersection_over_union`` from HITL. Scores heuristic/detector predictions
against fixture labels. Claim boundary: fixture_only / HEURISTIC_BASELINE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aerobim.domain.drawing_region_hitl import intersection_over_union

_CLAIM_BOUNDARY = (
    "fixture_only region detection metrics; heuristic baseline; "
    "not product CV; not customer accuracy"
)


@dataclass(frozen=True)
class RegionLabel:
    sheet_id: str
    layout_role: str
    bbox_xyxy: tuple[float, float, float, float]


@dataclass(frozen=True)
class RegionDetectionScore:
    tp: int
    fp: int
    fn: int
    iou_threshold: float
    matched: tuple[dict[str, Any], ...]
    claim_boundary: str = _CLAIM_BOUNDARY

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else (1.0 if self.fn == 0 else 0.0)

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 1.0

    @property
    def f1(self) -> float:
        denom = self.precision + self.recall
        return 2 * self.precision * self.recall / denom if denom else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f1": round(self.f1, 6),
            "iou_threshold": self.iou_threshold,
            "matched": list(self.matched),
            "claim_boundary": self.claim_boundary,
            "metric_note": "IoU@threshold role-matched P/R — not mAP product accuracy",
        }


def score_region_detections(
    predictions: list[RegionLabel],
    labels: list[RegionLabel],
    *,
    iou_threshold: float = 0.5,
) -> RegionDetectionScore:
    """Greedy one-to-one match: same sheet+role, IoU >= threshold."""

    used_labels: set[int] = set()
    matched: list[dict[str, Any]] = []
    tp = 0
    for pred in predictions:
        best_i = -1
        best_iou = 0.0
        for i, lab in enumerate(labels):
            if i in used_labels:
                continue
            if lab.sheet_id != pred.sheet_id or lab.layout_role != pred.layout_role:
                continue
            iou = intersection_over_union(pred.bbox_xyxy, lab.bbox_xyxy)
            if iou > best_iou:
                best_iou = iou
                best_i = i
        if best_i >= 0 and best_iou >= iou_threshold:
            used_labels.add(best_i)
            tp += 1
            matched.append(
                {
                    "sheet_id": pred.sheet_id,
                    "layout_role": pred.layout_role,
                    "iou": round(best_iou, 6),
                }
            )
    fp = len(predictions) - tp
    fn = len(labels) - tp
    return RegionDetectionScore(
        tp=tp,
        fp=fp,
        fn=fn,
        iou_threshold=iou_threshold,
        matched=tuple(matched),
    )


def labels_from_dicts(rows: list[dict[str, Any]]) -> list[RegionLabel]:
    out: list[RegionLabel] = []
    for row in rows:
        bbox = row.get("bbox_xyxy")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        out.append(
            RegionLabel(
                sheet_id=str(row.get("sheet_id") or ""),
                layout_role=str(row.get("layout_role") or ""),
                bbox_xyxy=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            )
        )
    return out


__all__ = [
    "RegionDetectionScore",
    "RegionLabel",
    "labels_from_dicts",
    "score_region_detections",
]
