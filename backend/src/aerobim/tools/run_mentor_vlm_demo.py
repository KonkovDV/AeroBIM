"""Mentor demo: region crop → Yandex VLM read → structured candidate (advisory only).

Shows that AeroBIM can *send a drawing crop* to Yandex AI Studio (Qwen) and get
back structured observations. Never flips ``summary.passed``.

Credentials (prefer product LLM env, fall back to Kimi smoke env):

- ``AEROBIM_LLM_BASE_URL`` / ``AEROBIM_LLM_API_KEY`` / ``AEROBIM_LLM_MODEL``
- optional ``AEROBIM_LLM_FOLDER_ID``, ``AEROBIM_LLM_AUTH_SCHEME`` (Api-Key)
- or ``AEROBIM_VLM_API_BASE_URL`` + ``AEROBIM_VLM_API_KEY``

Loads ``backend/.env`` when present (python-dotenv). Without keys → NOT_RUN exit 2.

Honesty: ``text_layer_present=False`` is **forced** so the VLM path runs even on
the open vector PDF (otherwise the plan skips VLM when a text layer exists).
Say this aloud on the call — deterministic text-layer path is the vertical slice;
this tool is the advisory vision path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.config.vlm_endpoint_gate import refuse_yandex_kimi_default_model
from aerobim.domain.models import DrawingSource
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.infrastructure.adapters.pdfium_region_cropper import PdfiumRegionCropper
from aerobim.infrastructure.adapters.region_restricted_vlm_pipeline import (
    RegionRestrictedVlmPipeline,
)
from aerobim.tools.vlm_smoke_gate import (
    evaluate_vlm_smoke_egress,
    gate_blocks_external,
    smoke_signoff_blocks_external,
    smoke_tenant_id,
)


def _observation_rows(
    pipeline: RegionRestrictedVlmPipeline, source: DrawingSource
) -> dict[str, Any]:
    """Richer mentor view: include grounded observation values (still advisory)."""
    result = pipeline.read_sheet(source, text_layer_present=False)
    reads: list[dict[str, Any]] = []
    for read in result.reads:
        reads.append(
            {
                "region_id": read.region_id,
                "degraded": read.degraded,
                "determinism_basis": read.determinism_basis,
                "crop_sha256": read.crop_sha256,
                "reason": read.reason,
                "control_fields_ignored": list(read.control_fields_ignored),
                "dropped_count": read.dropped_count,
                "observations": [
                    {
                        "kind": obs.kind,
                        "raw_value": obs.raw_value,
                        "normalized_value": obs.normalized_value,
                        "confidence": obs.confidence,
                        "hitl_required": obs.hitl_required,
                        "bbox_rel": list(obs.bbox_rel),
                        "evidence_note": obs.evidence_note,
                    }
                    for obs in read.observations
                ],
            }
        )
    produced = any(entry["observations"] for entry in reads)
    status = "skipped_vlm" if result.skipped_vlm else ("roundtrip_ok" if produced else "degraded")
    return {
        "status": status,
        "sheet_id": result.sheet_id,
        "skipped_vlm": result.skipped_vlm,
        "reason": result.reason,
        "regions_detected": result.regions_detected,
        "regions_planned": result.regions_planned,
        "regions_read": result.regions_read,
        "regions_truncated": result.regions_truncated,
        "stamp_regions_excluded": result.stamp_regions_excluded,
        "excluded_by_role": result.excluded_by_role,
        "reads": reads,
        "claim_boundary": (
            "roundtrip only, NOT a quality PASS; advisory candidate regions; "
            "cv_human_level MISSING; verdict stays with the deterministic engine and the expert"
        ),
    }


_SKIP_EXIT = 2
_BLOCKED_EXIT = 3
_FAIL_EXIT = 1


def _load_dotenv() -> Path | None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.is_file():
        return None
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
    except ImportError:
        # Minimal KEY=VALUE loader if dotenv missing in a stripped env.
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, _, val = s.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    return env_path


def _redact_model_uri(model: str) -> str:
    """Hide cloud folder id in gpt:// URIs for evidence packs."""
    if not model.startswith("gpt://"):
        return model
    parts = model.split("/")
    # gpt:// <folder> / <name> ...
    if len(parts) >= 4 and parts[0] == "gpt:" and parts[1] == "":
        return "gpt://<folder>/" + "/".join(parts[3:])
    return model


def _resolve_credentials() -> dict[str, str | None]:
    base = (
        os.getenv("AEROBIM_VLM_API_BASE_URL")
        or os.getenv("AEROBIM_LLM_BASE_URL")
        or os.getenv("AEROBIM_KIMI_API_BASE_URL")
        or ""
    ).strip()
    key = (
        os.getenv("AEROBIM_VLM_API_KEY")
        or os.getenv("AEROBIM_LLM_API_KEY")
        or os.getenv("AEROBIM_KIMI_API_KEY")
        or ""
    ).strip()
    model = (
        os.getenv("AEROBIM_VLM_MODEL")
        or os.getenv("AEROBIM_LLM_MODEL")
        or os.getenv("AEROBIM_KIMI_MODEL")
        or ""
    ).strip()
    folder = (os.getenv("AEROBIM_LLM_FOLDER_ID") or "").strip() or None
    auth = (os.getenv("AEROBIM_LLM_AUTH_SCHEME") or "Bearer").strip() or "Bearer"
    provider = (os.getenv("AEROBIM_LLM_PROVIDER") or "").strip() or None
    # Refuse silent kimi-k3 profile against Yandex Studio (wrong request shape).
    yandex_error = refuse_yandex_kimi_default_model(
        base_url=base or None, model=model or None, provider=provider
    )
    if yandex_error:
        return {
            "base_url": base or None,
            "api_key": key or None,
            "model": None,
            "folder_id": folder,
            "auth_scheme": auth,
            "provider": provider,
            "error": yandex_error,
        }
    if not model:
        model = "kimi-k3"
    return {
        "base_url": base or None,
        "api_key": key or None,
        "model": model,
        "folder_id": folder,
        "auth_scheme": auth,
        "provider": provider,
        "error": None,
    }


def _build_pipeline(
    *,
    base_url: str,
    api_key: str,
    model: str,
    auth_scheme: str,
    folder_id: str | None,
) -> RegionRestrictedVlmPipeline:
    from aerobim.infrastructure.adapters.vlm_advisory_client import VlmAdvisoryClient

    client = VlmAdvisoryClient(
        base_url=base_url,
        api_key=api_key,
        model=model,
        auth_scheme=auth_scheme,
        folder_id=folder_id,
        timeout_seconds=120.0,
    )
    return RegionRestrictedVlmPipeline(
        region_detector=HeuristicLayoutRegionDetector(),
        reader=client,
        cropper=PdfiumRegionCropper(coordinate_system="normalized-0-1", dpi=200),
        ready=True,
    )


def _save_planned_crops(
    *,
    source: DrawingSource,
    out_dir: Path,
    detector: HeuristicLayoutRegionDetector,
) -> list[dict[str, Any]]:
    """Save the same PII-clipped crops the pipeline would send (cloud-safe roles only)."""
    from aerobim.domain.region_read_plan import plan_region_reads
    from aerobim.infrastructure.adapters.pdf_page_orientation import read_page_rotate_degrees

    cropper = PdfiumRegionCropper(coordinate_system="normalized-0-1", dpi=200)
    crops_dir = out_dir / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    regions = detector.detect(source.path, sheet_id=source.sheet_id)  # type: ignore[arg-type]
    page_rotate = read_page_rotate_degrees(source.path) if source.path else 0
    plan = plan_region_reads(
        text_layer_present=False,
        regions=regions,
        exclude_stamp_regions=True,
        page_rotate_degrees=page_rotate,
    )
    saved: list[dict[str, Any]] = []
    for idx, task in enumerate(plan.tasks):
        role = task.layout_role or "unknown"
        png, media = cropper.crop(source, bbox_xyxy=task.bbox_xyxy)
        name = f"{idx:02d}-{role}.png"
        path = crops_dir / name
        path.write_bytes(png)
        saved.append(
            {
                "file": str(path.relative_to(out_dir)).replace("\\", "/"),
                "region_id": task.region_id,
                "layout_role": role,
                "bbox_xyxy": list(task.bbox_xyxy),
                "coordinate_system": task.coordinate_system,
                "media_type": media,
                "sha256": hashlib.sha256(png).hexdigest(),
                "bytes": len(png),
                "egress_crop": True,
            }
        )
    return saved


def _limitations(*, live: bool, model: str, provider: str | None) -> dict[str, Any]:
    return {
        "claim_boundary": (
            "advisory VLM region read only; roundtrip / structured candidate; "
            "NOT product CV; NOT >90% accuracy; NEVER flips summary.passed"
        ),
        "provider": provider or "unknown",
        "model": _redact_model_uri(model),
        "live_call": live,
        "forced_vlm_path": True,
        "forced_vlm_path_reason": (
            "text_layer_present=False so mentor can see crop→VLM; "
            "deterministic text-layer path is vertical-slice demo"
        ),
        "do_not_claim": [
            "trained LayoutLMv3 / DocLayNet in product",
            "native DWG",
            "whole-sheet VLM as production path",
            "VLM decides PASS/FAIL",
            "customer accuracy >90%",
        ],
        "honest_claims": [
            "Yandex AI Studio OpenAI-compat endpoint wired",
            "region crop only (stamp excluded by plan)",
            "structured observations schema with candidate_class",
            "ADR-001 advisory OFF==ON for verdict",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("../samples/demo/vertical-slice-2026-08-11/techlab-a101-wall-thickness.pdf"),
        help="Open-data sheet PDF",
    )
    parser.add_argument("--sheet-id", default="TECHLAB-A101")
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../artifacts/mentor-vlm-2026-08-11"),
        help="Artifact directory",
    )
    parser.add_argument(
        "--dry-crop-only",
        action="store_true",
        help="Save crops + limitations without calling VLM (offline rehearsal)",
    )
    args = parser.parse_args(argv)

    env_path = _load_dotenv()
    creds = _resolve_credentials()
    out_dir = args.output
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf = args.pdf
    if not pdf.is_file():
        # Resolve relative to repo root when launched from backend/
        alt = (
            Path(__file__).resolve().parents[4]
            / "samples/demo/vertical-slice-2026-08-11"
            / pdf.name
        )
        if alt.is_file():
            pdf = alt
        else:
            print(json.dumps({"status": "NOT_RUN", "reason": f"pdf not found: {args.pdf}"}))
            return _SKIP_EXIT

    source = DrawingSource(path=pdf, sheet_id=args.sheet_id)
    detector = HeuristicLayoutRegionDetector()
    crops = _save_planned_crops(source=source, out_dir=out_dir, detector=detector)

    if args.dry_crop_only:
        dry_report = {
            "status": "dry_crop_only",
            "sheet_id": args.sheet_id,
            "pdf": str(pdf),
            "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "crops": crops,
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "dotenv_loaded": str(env_path) if env_path else None,
            "claim_boundary": _limitations(
                live=False, model=creds["model"] or "", provider=creds["provider"]
            )["claim_boundary"],
        }
        (out_dir / "report.json").write_text(
            json.dumps(dry_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out_dir / "LIMITATIONS.json").write_text(
            json.dumps(
                _limitations(live=False, model=creds["model"] or "", provider=creds["provider"]),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(dry_report, ensure_ascii=False, indent=2))
        return 0

    if creds.get("error"):
        bad = {
            "status": "NOT_RUN",
            "reason": creds["error"],
            "crops": crops,
            "dotenv_loaded": str(env_path) if env_path else None,
        }
        print(json.dumps(bad, ensure_ascii=False, indent=2))
        (out_dir / "report.json").write_text(
            json.dumps(bad, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return _SKIP_EXIT

    if not creds["base_url"] or not creds["api_key"]:
        skip = {
            "status": "NOT_RUN",
            "reason": (
                "set AEROBIM_VLM_API_BASE_URL + AEROBIM_VLM_API_KEY "
                "(or AEROBIM_LLM_* / deprecated AEROBIM_KIMI_*); dotenv_loaded="
                f"{bool(env_path)}"
            ),
            "crops": crops,
            "dotenv_loaded": str(env_path) if env_path else None,
        }
        print(json.dumps(skip, ensure_ascii=False, indent=2))
        (out_dir / "report.json").write_text(
            json.dumps(skip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return _SKIP_EXIT

    signoff_block = smoke_signoff_blocks_external()
    if signoff_block:
        blocked = {
            "status": "BLOCKED_BY_SIGNOFF",
            "reason": signoff_block,
            "may_call_external": False,
            "crops": crops,
            "claim_boundary": "pilot/production forbids external VLM smoke",
        }
        print(json.dumps(blocked, ensure_ascii=False, indent=2))
        return _BLOCKED_EXIT

    tenant = smoke_tenant_id(args.tenant_id)
    gate_result = evaluate_vlm_smoke_egress(
        tenant_id=tenant, sheet_id=args.sheet_id, image_name=pdf.name
    )
    if gate_blocks_external(gate_result):
        blocked = {
            "status": "BLOCKED_BY_GATE",
            "reason": gate_result.decision.reason,
            "may_call_external": False,
            "crops": crops,
            "claim_boundary": "HybridRouteGate refused PUBLIC VLM egress; zero bytes sent",
        }
        print(json.dumps(blocked, ensure_ascii=False, indent=2))
        return _BLOCKED_EXIT

    assert creds["base_url"] and creds["api_key"] and creds["model"]
    try:
        pipeline = _build_pipeline(
            base_url=creds["base_url"],
            api_key=creds["api_key"],
            model=creds["model"],
            auth_scheme=creds["auth_scheme"] or "Bearer",
            folder_id=creds["folder_id"],
        )
        # Forced advisory VLM path for mentor — see LIMITATIONS.forced_vlm_path_reason.
        smoke = _observation_rows(pipeline, source)
    except Exception as exc:
        fail = {
            "status": "LIVE_ERROR",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "crops": crops,
            "model": creds["model"],
            "provider": creds["provider"],
            "auth_scheme": creds["auth_scheme"],
            "folder_id_set": bool(creds["folder_id"]),
            "base_host": (creds["base_url"] or "").split("/")[2] if creds["base_url"] else None,
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "claim_boundary": _limitations(
                live=False, model=creds["model"] or "", provider=creds["provider"]
            )["claim_boundary"],
        }
        (out_dir / "report.json").write_text(
            json.dumps(fail, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out_dir / "LIMITATIONS.json").write_text(
            json.dumps(
                _limitations(live=False, model=creds["model"] or "", provider=creds["provider"]),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps(fail, ensure_ascii=False, indent=2))
        return _FAIL_EXIT

    report: dict[str, Any] = {
        **smoke,
        "pdf": str(pdf),
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "crops": crops,
        "model": _redact_model_uri(creds["model"] or ""),
        "provider": creds["provider"],
        "auth_scheme": creds["auth_scheme"],
        "folder_id_set": bool(creds["folder_id"]),
        "forced_text_layer_present": False,
        "dotenv_loaded": str(env_path) if env_path else None,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "talking_points_ru": [
            "1) Deterministic vertical slice: PDF text-layer -> finding (not VLM).",
            "2) This run: region crop -> Yandex Qwen -> JSON observations (advisory).",
            "3) Stamp excluded; whole sheet is never sent to the model.",
            "4) summary.passed is never changed by VLM (ADR-001 / OFF==ON).",
            "5) Do not claim product CV / >90% / native DWG.",
        ],
    }
    limits = _limitations(live=True, model=creds["model"] or "", provider=creds["provider"])
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out_dir / "LIMITATIONS.json").write_text(
        json.dumps(limits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "roundtrip_ok" else _FAIL_EXIT


if __name__ == "__main__":
    sys.exit(main())
