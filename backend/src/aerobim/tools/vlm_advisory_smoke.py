"""One-shot live smoke for the advisory VLM read (OPEN DATA ONLY).

Purpose: prove the real endpoint returns a payload the grounding parser accepts,
BEFORE the VLM/OCR protocol — so the protocol starts with measurements,
not schema debugging.

Safety: this makes a real outbound call. Run it ONLY on non-NDA / open sample
images. Requires ``AEROBIM_VLM_API_BASE_URL`` + ``AEROBIM_VLM_API_KEY``
(deprecated aliases: ``AEROBIM_KIMI_*``); without them it prints NOT_RUN and
exits 2 (skip, never a fake pass). The verdict path is untouched — advisory only.

WP-02 residual: ``HybridRouteGate`` MUST pass before constructing the VLM client.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aerobim.core.config.vlm_endpoint_gate import refuse_yandex_kimi_default_model
from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.vlm_advisory_client import (
    VlmAdvisoryClient,
    VlmAdvisoryError,
)
from aerobim.infrastructure.adapters.vlm_drawing_pipeline import VlmDrawingPipeline
from aerobim.tools.vlm_smoke_gate import (
    evaluate_vlm_smoke_egress,
    gate_blocks_external,
    smoke_signoff_blocks_external,
    smoke_tenant_id,
)

_SKIP_EXIT = 2
_BLOCKED_EXIT = 3


def run_smoke(
    image: Path,
    *,
    sheet_id: str,
    tenant_id: str | None = None,
    client_factory: Callable[..., Any] | None = None,
    allow_whole_sheet: bool = False,
) -> dict[str, object]:
    base_url = (
        os.getenv("AEROBIM_VLM_API_BASE_URL") or os.getenv("AEROBIM_KIMI_API_BASE_URL") or ""
    ).strip()
    api_key = (os.getenv("AEROBIM_VLM_API_KEY") or os.getenv("AEROBIM_KIMI_API_KEY") or "").strip()
    model = (
        os.getenv("AEROBIM_VLM_MODEL") or os.getenv("AEROBIM_KIMI_MODEL") or "kimi-k3"
    ).strip() or "kimi-k3"
    reasoning = (
        os.getenv("AEROBIM_VLM_REASONING_EFFORT")
        or os.getenv("AEROBIM_KIMI_REASONING_EFFORT")
        or "low"
    ).strip().lower() or "low"
    if not base_url or not api_key:
        return {
            "status": "NOT_RUN",
            "reason": (
                "set AEROBIM_VLM_API_BASE_URL and AEROBIM_VLM_API_KEY "
                "(or deprecated AEROBIM_KIMI_* aliases; open data only)"
            ),
        }
    if not image.is_file():
        return {"status": "NOT_RUN", "reason": f"image not found: {image}"}
    if not allow_whole_sheet:
        return {
            "status": "NOT_RUN",
            "reason": (
                "whole-sheet VLM smoke is deprecated (stamp/PII risk); "
                "use aerobim.tools.vlm_region_smoke, or pass --allow-whole-sheet "
                "explicitly for open-data raster fixtures only"
            ),
        }

    yandex_block = refuse_yandex_kimi_default_model(
        base_url=base_url,
        model=model,
        provider=(os.getenv("AEROBIM_LLM_PROVIDER") or "").strip() or None,
    )
    if yandex_block:
        return {"status": "NOT_RUN", "reason": yandex_block}

    signoff_block = smoke_signoff_blocks_external()
    if signoff_block:
        return {
            "status": "BLOCKED_BY_SIGNOFF",
            "reason": signoff_block,
            "may_call_external": False,
            "claim_boundary": "pilot/production forbids external VLM smoke",
        }

    tenant = smoke_tenant_id(tenant_id)
    gate_result = evaluate_vlm_smoke_egress(
        tenant_id=tenant,
        sheet_id=sheet_id,
        image_name=image.name,
    )
    if gate_blocks_external(gate_result):
        return {
            "status": "BLOCKED_BY_GATE",
            "reason": gate_result.decision.reason,
            "may_call_external": False,
            "egress_bytes_estimate": gate_result.egress_bytes_estimate,
            "claim_boundary": ("HybridRouteGate refused PUBLIC VLM egress; zero bytes sent"),
        }

    if client_factory is not None:
        client = client_factory(
            base_url=base_url, api_key=api_key, model=model, reasoning=reasoning
        )
    else:
        client = VlmAdvisoryClient(
            base_url=base_url, api_key=api_key, model=model, reasoning_effort=reasoning
        )
    pipeline = VlmDrawingPipeline(client, ready=True, model_id=model)
    try:
        result = pipeline.analyze(DrawingSource(path=image, sheet_id=sheet_id), mode="auto")
    except VlmAdvisoryError as exc:  # pipeline degrades, but guard anyway
        return {"status": "FAILED", "reason": str(exc)}

    schema_ok = result.pipeline_mode_used == "vlm_candidate"
    return {
        "status": "OK" if schema_ok else "DEGRADED",
        "model": model,
        "pipeline_mode": result.pipeline_mode_used,
        "regions": len(result.regions),
        "hitl_low_confidence": sum(1 for r in result.regions if r.hitl_required),
        "degraded": result.degraded,
        "reason": result.reason,
        "may_call_external": True,
        "whole_sheet": True,
        "claim_boundary": (
            "advisory candidate regions only; whole-sheet path is legacy/open-data; "
            "prefer region-restricted smoke; verdict stays deterministic"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="OPEN-DATA image (png/jpg/webp)")
    parser.add_argument("--sheet-id", default="SMOKE-01")
    parser.add_argument("--tenant-id", default=None, help="Hybrid tenant (default open-data-smoke)")
    parser.add_argument(
        "--allow-whole-sheet",
        action="store_true",
        help="Explicit opt-in to deprecated whole-sheet VLM (open-data rasters only)",
    )
    args = parser.parse_args(argv)

    report = run_smoke(
        args.image,
        sheet_id=args.sheet_id,
        tenant_id=args.tenant_id,
        allow_whole_sheet=args.allow_whole_sheet,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "NOT_RUN":
        return _SKIP_EXIT
    if report["status"] in {"BLOCKED_BY_GATE", "BLOCKED_BY_SIGNOFF"}:
        return _BLOCKED_EXIT
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
