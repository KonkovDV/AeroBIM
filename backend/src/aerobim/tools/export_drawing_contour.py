"""Export a drawing-contour assessment over a synthetic sheet (P1, verdict-neutral).

Демонстрирует P1 drawing-контур (quality gate -> classifier -> assessment) на
СИНТЕТИЧЕСКОМ листе зон: хороший штамп/спецификация (AUTO_READ), низкокачественная и
нечитаемая зоны (EXPERT_REVIEW, без классификации — anti-bad-scan), неоднозначная зона
(UNKNOWN -> EXPERT_REVIEW) и зона без сигналов (REVIEW_REQUIRED). Без данных заказчика,
без сети, verdict-neutral (не выставляет summary.passed, ADR-001). Checkpoint GO (regulatory_measurement_mvp; customer_go false).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.drawing_region_assessment import RegionAction, assess_drawing_region
from aerobim.domain.region_quality import RegionQualitySignals

# Synthetic, de-identified regions: (label, text, dpi, skew, has_text, chars).
_SCENARIO: tuple[dict[str, Any], ...] = (
    {"label": "titleblock", "text": "Стадия П Изм. Разраб.", "dpi": 300, "skew": 1.0, "chars": 40},
    {
        "label": "spec",
        "text": "Спецификация Поз. Наименование Кол.",
        "dpi": 300,
        "skew": 0.5,
        "chars": 60,
    },
    {"label": "low-quality-node", "text": "Узел А", "dpi": 120, "skew": 1.0, "chars": 6},
    {"label": "unreadable-scan", "text": "Разрез 1-1", "dpi": 50, "skew": 1.0, "chars": 8},
    {"label": "ambiguous", "text": "Разрез фасад", "dpi": 300, "skew": 1.0, "chars": 12},
    {"label": "no-signal", "text": "Узел Б"},
)


def synthetic_scenario() -> dict[str, Any]:
    """Build a fixed SYNTHETIC sheet and return the drawing-contour assessment."""
    regions: list[dict[str, Any]] = []
    counts = {action.value: 0 for action in RegionAction}
    by_quality: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for spec in _SCENARIO:
        signals = RegionQualitySignals(
            dpi=spec.get("dpi"),
            skew_deg=spec.get("skew"),
            has_text=True if "chars" in spec else None,
            text_char_count=spec.get("chars"),
        )
        result = assess_drawing_region(text=spec.get("text"), quality_signals=signals)
        region_type = (
            result.classification.region_type.value if result.classification is not None else None
        )
        regions.append(
            {
                "label": spec["label"],
                "action": result.action.value,
                "quality": result.quality.value,
                "region_type": region_type,
                "reasons": list(result.reasons),
            }
        )
        counts[result.action.value] += 1
        by_quality[result.quality.value] = by_quality.get(result.quality.value, 0) + 1
        if region_type is not None:
            by_type[region_type] = by_type.get(region_type, 0) + 1

    return {
        "artifact": "drawing-contour",
        "corpus": "synthetic",
        "disclaimer": "synthetic fixture; no customer data; not product accuracy",
        "note": (
            "quality gate -> (if readable) type classifier; bad/unknown/ambiguous -> expert "
            "review, never auto-read; verdict-neutral (does NOT set summary.passed, ADR-001)"
        ),
        "regions": regions,
        "summary": {"actions": counts, "by_quality": by_quality, "by_type": by_type},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a synthetic drawing-contour assessment.")
    parser.add_argument("--output", type=Path, default=None, help="write JSON here (else stdout)")
    args = parser.parse_args(argv)
    text = json.dumps(synthetic_scenario(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
