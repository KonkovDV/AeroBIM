"""Evaluate heuristic region detections against fixture labels (P1.2).

Claim boundary: fixture_only IoU@50 P/R — not product CV / not customer accuracy.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.region_detection_metrics import (
    labels_from_dicts,
    score_region_detections,
)
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)


def _preds_from_detector(pdf: Path, sheet_id: str) -> list[dict[str, Any]]:
    regions = HeuristicLayoutRegionDetector().detect(pdf, sheet_id=sheet_id)
    return [
        {
            "sheet_id": r.sheet_id,
            "layout_role": r.layout_role or "",
            "bbox_xyxy": list(r.bbox_xyxy),
        }
        for r in regions
    ]


def evaluate(
    *,
    pdf: Path,
    labels_path: Path,
    sheet_id: str,
    iou_threshold: float,
) -> dict[str, Any]:
    labels_payload = json.loads(labels_path.read_text(encoding="utf-8"))
    label_rows = (
        labels_payload.get("regions") if isinstance(labels_payload, dict) else labels_payload
    )
    if not isinstance(label_rows, list):
        raise ValueError("labels must be a list or {regions: [...]}")
    preds = labels_from_dicts(_preds_from_detector(pdf, sheet_id))
    labels = labels_from_dicts(label_rows)
    score = score_region_detections(preds, labels, iou_threshold=iou_threshold)
    return {
        "artifact_type": "region_detection_eval",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "pdf": str(pdf),
        "labels": str(labels_path),
        "sheet_id": sheet_id,
        "prediction_count": len(preds),
        "label_count": len(labels),
        "score": score.as_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--sheet-id", default="A-101")
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = evaluate(
        pdf=args.pdf,
        labels_path=args.labels,
        sheet_id=args.sheet_id,
        iou_threshold=args.iou_threshold,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
