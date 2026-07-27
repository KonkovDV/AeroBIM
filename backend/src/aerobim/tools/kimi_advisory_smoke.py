"""One-shot live smoke for the Kimi advisory VLM read (tier A, OPEN DATA ONLY).

Purpose: prove the real endpoint returns a payload the grounding parser accepts,
BEFORE the Aug 4-20 VLM/OCR protocol — so the protocol starts with measurements,
not schema debugging.

Safety: this makes a real outbound call. Run it ONLY on non-NDA / open sample
images (tier A). Requires ``AEROBIM_KIMI_API_BASE_URL`` + ``AEROBIM_KIMI_API_KEY``;
without them it prints a NOT_RUN status and exits 2 (skip, never a fake pass).
The verdict path is untouched — this is an advisory read only.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.kimi_k3_advisory_client import (
    KimiAdvisoryError,
    KimiK3AdvisoryClient,
)
from aerobim.infrastructure.adapters.kimi_vlm_drawing_pipeline import KimiVlmDrawingPipeline

_SKIP_EXIT = 2


def run_smoke(image: Path, *, sheet_id: str) -> dict[str, object]:
    base_url = (os.getenv("AEROBIM_KIMI_API_BASE_URL") or "").strip()
    api_key = (os.getenv("AEROBIM_KIMI_API_KEY") or "").strip()
    model = (os.getenv("AEROBIM_KIMI_MODEL") or "kimi-k3").strip() or "kimi-k3"
    reasoning = (os.getenv("AEROBIM_KIMI_REASONING_EFFORT") or "low").strip().lower() or "low"
    if not base_url or not api_key:
        return {
            "status": "NOT_RUN",
            "reason": (
                "set AEROBIM_KIMI_API_BASE_URL and AEROBIM_KIMI_API_KEY (tier A open data only)"
            ),
        }
    if not image.is_file():
        return {"status": "NOT_RUN", "reason": f"image not found: {image}"}

    client = KimiK3AdvisoryClient(
        base_url=base_url, api_key=api_key, model=model, reasoning_effort=reasoning
    )
    pipeline = KimiVlmDrawingPipeline(client, ready=True, model_id=model)
    try:
        result = pipeline.analyze(DrawingSource(path=image, sheet_id=sheet_id), mode="auto")
    except KimiAdvisoryError as exc:  # pipeline degrades, but guard anyway
        return {"status": "FAILED", "reason": str(exc)}

    schema_ok = result.pipeline_mode_used == "kimi_vlm_candidate"
    return {
        "status": "OK" if schema_ok else "DEGRADED",
        "model": model,
        "pipeline_mode": result.pipeline_mode_used,
        "regions": len(result.regions),
        "hitl_low_confidence": sum(1 for r in result.regions if r.hitl_required),
        "degraded": result.degraded,
        "reason": result.reason,
        "claim_boundary": "advisory candidate regions only; verdict stays deterministic",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="OPEN-DATA image (png/jpg/webp)")
    parser.add_argument("--sheet-id", default="SMOKE-01")
    args = parser.parse_args(argv)

    report = run_smoke(args.image, sheet_id=args.sheet_id)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "NOT_RUN":
        return _SKIP_EXIT
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
