"""Region-restricted live smoke for the advisory VLM (tier A, OPEN DATA ONLY).

Exercises the real §3 path — layout detector → read plan → PyMuPDF crop → ONE
``read_region`` call per region (never the whole sheet) → §4 observations
grounding — optionally through the §2.1 deterministic cache. Purpose: prove the
real endpoint round-trips through our parser BEFORE the Aug 4-20 protocol, and
(with ``--cache-dir``) that a second run replays byte-identically without a call.

Safety: makes real outbound calls; run ONLY on non-NDA / open sample images.
Requires ``AEROBIM_KIMI_API_BASE_URL`` + ``AEROBIM_KIMI_API_KEY``; without them
it prints NOT_RUN and exits 2 (a skip, never a fabricated pass). Advisory only —
the deterministic verdict is untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.infrastructure.adapters.pymupdf_region_cropper import PyMuPDFRegionCropper
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)

_SKIP_EXIT = 2


def build_region_smoke_report(
    pipeline: RegionRestrictedVlmPipeline,
    source: DrawingSource,
    *,
    text_layer_present: bool = False,
) -> dict[str, Any]:
    """Run the region-restricted pipeline and summarize (advisory candidates only)."""
    result = pipeline.read_sheet(source, text_layer_present=text_layer_present)
    reads = [
        {
            "region_id": read.region_id,
            "observations": len(read.observations),
            "hitl_low_confidence": sum(1 for obs in read.observations if obs.hitl_required),
            "degraded": read.degraded,
            "determinism_basis": read.determinism_basis,
            "crop_sha256": read.crop_sha256,
            "reason": read.reason,
        }
        for read in result.reads
    ]
    produced = any(entry["observations"] for entry in reads)
    if result.skipped_vlm:
        status = "skipped_vlm"
    elif produced:
        # NOT a quality PASS: only that a real response round-tripped through our
        # parser. Quality/completeness/coordinates vs a reference are unproven.
        status = "roundtrip_ok"
    else:
        status = "degraded"
    return {
        "status": status,
        "sheet_id": result.sheet_id,
        "skipped_vlm": result.skipped_vlm,
        "reason": result.reason,
        "regions_detected": result.regions_detected,
        "regions_planned": result.regions_planned,
        "regions_read": result.regions_read,
        "regions_truncated": result.regions_truncated,
        "truncation_reason": result.truncation_reason,
        "region_plan_sha256": result.region_plan_sha256,
        "reads": reads,
        "claim_boundary": (
            "roundtrip only, NOT a quality PASS; advisory candidate regions; "
            "cv_human_level MISSING; verdict stays with the deterministic engine and the expert"
        ),
    }


def _build_pipeline(
    *, base_url: str, api_key: str, model: str, reasoning: str, cache_dir: str | None
) -> RegionRestrictedVlmPipeline:
    from aerobim.infrastructure.adapters.kimi_k3_advisory_client import VlmAdvisoryClient

    client = VlmAdvisoryClient(
        base_url=base_url, api_key=api_key, model=model, reasoning_effort=reasoning
    )
    reader: object = client
    if cache_dir:
        from aerobim.infrastructure.adapters.caching_vlm_reader import (
            CachingVlmReader,
            FilesystemVlmResponseStore,
        )
        from aerobim.infrastructure.adapters.kimi_k3_advisory_client import (
            observations_schema_hash,
        )

        reader = CachingVlmReader(
            client,
            FilesystemVlmResponseStore(Path(cache_dir)),
            model=model,
            endpoint=base_url,
            request_schema_hash=observations_schema_hash(),
        )
    return RegionRestrictedVlmPipeline(
        region_detector=HeuristicLayoutRegionDetector(),
        reader=reader,  # type: ignore[arg-type]
        cropper=PyMuPDFRegionCropper(),
        ready=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True, help="OPEN-DATA sheet (pdf/png/jpg)")
    parser.add_argument("--sheet-id", default="SMOKE-01")
    parser.add_argument("--cache-dir", default=None, help="§2.1 cache dir (enables replay)")
    parser.add_argument("--out", type=Path, default=None, help="artifact path (JSON)")
    args = parser.parse_args(argv)

    base_url = (os.getenv("AEROBIM_KIMI_API_BASE_URL") or "").strip()
    api_key = (os.getenv("AEROBIM_KIMI_API_KEY") or "").strip()
    model = (os.getenv("AEROBIM_KIMI_MODEL") or "kimi-k3").strip() or "kimi-k3"
    reasoning = (os.getenv("AEROBIM_KIMI_REASONING_EFFORT") or "low").strip().lower() or "low"
    cache_dir = args.cache_dir or (os.getenv("AEROBIM_KIMI_CACHE_DIR") or "").strip() or None

    if not base_url or not api_key:
        print(
            json.dumps(
                {
                    "status": "NOT_RUN",
                    "reason": (
                        "set AEROBIM_KIMI_API_BASE_URL and AEROBIM_KIMI_API_KEY (tier A open data)"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return _SKIP_EXIT
    if not args.image.is_file():
        print(json.dumps({"status": "NOT_RUN", "reason": f"image not found: {args.image}"}))
        return _SKIP_EXIT

    pipeline = _build_pipeline(
        base_url=base_url, api_key=api_key, model=model, reasoning=reasoning, cache_dir=cache_dir
    )
    source = DrawingSource(path=args.image, sheet_id=args.sheet_id)
    report = build_region_smoke_report(pipeline, source)
    report.update(
        model=model,
        image_sha256=hashlib.sha256(args.image.read_bytes()).hexdigest(),
        cache_enabled=bool(cache_dir),
        generated_at=datetime.now(tz=UTC).isoformat(),
    )

    out = args.out or (
        Path(__file__).resolve().parents[4]
        / "audit"
        / "evidence"
        / f"kimi-region-smoke-{datetime.now(tz=UTC):%Y-%m-%d}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "roundtrip_ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
