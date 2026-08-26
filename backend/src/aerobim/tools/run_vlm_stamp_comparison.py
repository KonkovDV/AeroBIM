"""Kimi vs Qwen stamp/title-block comparison contour.

Loads ``backend/.env``. Advisory-only. Never sets summary.passed.
Invalid JSON → fail-closed (zero score for that region). Not door/window counting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from aerobim.core.config.vlm_endpoint_gate import refuse_yandex_kimi_default_model
from aerobim.domain.models import DrawingSource
from aerobim.tools.benchmark_project_package import _machine_fingerprint, repo_root
from aerobim.tools.run_mentor_vlm_demo import (
    _build_pipeline,
    _load_dotenv,
    _observation_rows,
    _redact_model_uri,
    _resolve_credentials,
)
from aerobim.tools.vlm_smoke_gate import (
    evaluate_vlm_smoke_egress,
    gate_blocks_external,
    smoke_signoff_blocks_external,
    smoke_tenant_id,
)

CLAIM_BOUNDARY = (
    "VLM advisory on open fixture title-block/spec crops. Stamp pixels are not "
    "sent (PII clip). fixture_only. Not door/window counting. Not product accuracy. "
    "Invalid JSON → fail-closed skip for that region."
)

# Order-of-magnitude Studio list (RUB / 1K tokens) — not billing SSOT.
_RUB_PER_1K = {"input": 0.20, "output": 0.40}


def build_vlm_comparison(*, api_key_present: bool) -> dict[str, Any]:
    """Offline shape used by unit tests; live path is ``run_stamp_comparison``."""
    status = "RUNNABLE" if api_key_present else "SKIPPED"
    reason = None if api_key_present else "AEROBIM_LLM_API_KEY not set — refuse to invent metrics"
    payload: dict[str, Any] = {
        "artifact_type": "vlm_stamp_comparison",
        "schema_version": "1.1.0",
        "claim_level": "fixture_only",
        "claim_boundary": CLAIM_BOUNDARY,
        "scenario": "stamp_title_block_explication",
        "not_in_scope": ["door_count", "window_count", "whole_sheet_geometry"],
        "models": [
            {"id": "qwen3-vl", "route": "Yandex AI Studio allowlisted host", "role": "primary"},
            {
                "id": "kimi",
                "route": "refused on Yandex host (kimi-k3 default gate)",
                "role": "not_run_on_studio",
            },
        ],
        "comparison_status": "comparison_not_run",
        "comparison_reason": (
            "Qwen and Kimi were not executed on the same input, prompt, and "
            "output schema in one repeatable artifact. Do not invent a bake-off."
        ),
        "qwen_fixture_status": "not_run_in_this_payload",
        "kimi_status": "GATED",
        "status": status,
        "skip_reason": reason,
        "metrics": None,
        "recommendation": ("No live scores this run. Do not pick a model from empty metrics."),
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "machine": _machine_fingerprint(),
        "customer_accuracy_not_established": True,
    }
    raw = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    payload["content_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload


def _spot_checks(reads: list[dict[str, Any]]) -> dict[str, Any]:
    blob = json.dumps(reads, ensure_ascii=False).lower()
    return {
        "mentions_wall_01": "wall-01" in blob or "wall_01" in blob,
        "mentions_150": "150" in blob,
        "note": "Open-fixture substring checks, not adjudicated precision/recall",
    }


def run_stamp_comparison(*, pdf: Path, sheet_id: str) -> dict[str, Any]:
    env_path = _load_dotenv()
    creds = _resolve_credentials()
    kimi_refuse = refuse_yandex_kimi_default_model(
        base_url=str(creds.get("base_url") or "") or None,
        model="kimi-k3",
        provider=str(creds.get("provider") or "") or None,
    )
    kimi_row = {
        "id": "kimi",
        "status": "GATE_REFUSED" if kimi_refuse else "NOT_CONFIGURED",
        "reason": kimi_refuse or "No separate non-Yandex Kimi endpoint in env; not invented",
        "metrics": None,
    }

    key_present = bool(creds.get("api_key"))
    if creds.get("error"):
        payload = build_vlm_comparison(api_key_present=key_present)
        payload["status"] = "NOT_RUN"
        payload["skip_reason"] = str(creds["error"])
        payload["dotenv_loaded"] = bool(env_path)
        payload["models_run"] = [kimi_row]
        return payload
    if not creds.get("base_url") or not creds.get("api_key") or not creds.get("model"):
        payload = build_vlm_comparison(api_key_present=False)
        payload["skip_reason"] = (
            f"LLM/VLM key or base_url missing after dotenv (dotenv_loaded={bool(env_path)})"
        )
        payload["dotenv_loaded"] = bool(env_path)
        payload["models_run"] = [kimi_row]
        return payload

    signoff_block = smoke_signoff_blocks_external()
    if signoff_block:
        payload = build_vlm_comparison(api_key_present=True)
        payload["status"] = "BLOCKED_BY_SIGNOFF"
        payload["skip_reason"] = signoff_block
        payload["models_run"] = [kimi_row]
        return payload

    tenant = smoke_tenant_id(None)
    gate_result = evaluate_vlm_smoke_egress(
        tenant_id=tenant, sheet_id=sheet_id, image_name=pdf.name
    )
    if gate_blocks_external(gate_result):
        payload = build_vlm_comparison(api_key_present=True)
        payload["status"] = "BLOCKED_BY_GATE"
        payload["skip_reason"] = gate_result.decision.reason
        payload["models_run"] = [kimi_row]
        return payload

    source = DrawingSource(path=pdf, sheet_id=sheet_id)
    host = urlparse(str(creds["base_url"])).hostname or "unknown"
    started = perf_counter()
    try:
        pipeline = _build_pipeline(
            base_url=str(creds["base_url"]),
            api_key=str(creds["api_key"]),
            model=str(creds["model"]),
            auth_scheme=str(creds.get("auth_scheme") or "Bearer"),
            folder_id=creds.get("folder_id") if isinstance(creds.get("folder_id"), str) else None,
        )
        smoke = _observation_rows(pipeline, source)
    except Exception as exc:
        elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
        payload = build_vlm_comparison(api_key_present=True)
        payload["status"] = "LIVE_ERROR"
        payload["skip_reason"] = f"{type(exc).__name__}: {str(exc)[:240]}"
        payload["dotenv_loaded"] = bool(env_path)
        payload["models_run"] = [
            {
                "id": "qwen",
                "status": "LIVE_ERROR",
                "host": host,
                "model": _redact_model_uri(str(creds["model"])),
                "elapsed_ms": elapsed_ms,
            },
            kimi_row,
        ]
        payload["recommendation"] = (
            "Live Qwen call failed; do not invent scores. Fix Studio/network and re-run."
        )
        return payload

    elapsed_ms = round((perf_counter() - started) * 1000.0, 1)
    reads = list(smoke.get("reads") or [])
    regions_read = int(smoke.get("regions_read") or 0)
    degraded = sum(1 for row in reads if isinstance(row, dict) and row.get("degraded"))
    obs_n = sum(len(row.get("observations") or []) for row in reads if isinstance(row, dict))
    schema_fail_regions = sum(
        1
        for row in reads
        if isinstance(row, dict) and row.get("degraded") and not row.get("observations")
    )
    schema_fail_share = round(schema_fail_regions / regions_read, 4) if regions_read else None
    qwen_row = {
        "id": "qwen",
        "status": smoke.get("status"),
        "host": host,
        "model": _redact_model_uri(str(creds["model"])),
        "elapsed_ms": elapsed_ms,
        "regions_detected": smoke.get("regions_detected"),
        "regions_planned": smoke.get("regions_planned"),
        "regions_read": regions_read,
        "stamp_regions_excluded": smoke.get("stamp_regions_excluded"),
        "observation_count": obs_n,
        "degraded_regions": degraded,
        "schema_fail_region_share": schema_fail_share,
        "spot_checks": _spot_checks(reads),
        "skipped_vlm": smoke.get("skipped_vlm"),
        "pipeline_reason": smoke.get("reason"),
        "cost_note": (
            "Token usage is per-region inside the client; pack-level RUB is not "
            "aggregated here without usage on each read. Order-of-magnitude only."
        ),
        "rub_per_1k_tokens_assumed": _RUB_PER_1K,
    }
    take_qwen = smoke.get("status") == "roundtrip_ok" and kimi_row["status"] == "GATE_REFUSED"
    payload = build_vlm_comparison(api_key_present=True)
    payload["status"] = "LIVE"
    payload["qwen_fixture_status"] = "LIVE"
    payload["kimi_status"] = "GATED"
    payload["comparison_status"] = "comparison_not_run"
    payload["skip_reason"] = None
    payload["dotenv_loaded"] = bool(env_path)
    payload["metrics"] = {
        "n_sheets": 1,
        "corpus": "open_fixture_vertical_slice_pdf",
        "qwen": qwen_row,
        "kimi": kimi_row,
    }
    payload["models_run"] = [qwen_row, kimi_row]
    payload["recommendation"] = (
        "Qwen is LIVE on this open fixture (structured roundtrip recorded). "
        "Kimi is GATED on the Studio host. comparison_status=comparison_not_run: "
        "same input/prompt/schema was not executed for both models. "
        "Not a bake-off. Not product accuracy. Does not close RT-001."
        if take_qwen
        else (
            "Live Qwen path completed; Kimi remains gated. "
            "comparison_status=comparison_not_run. Do not publish as product accuracy."
        )
    )
    raw = json.dumps(
        {k: v for k, v in payload.items() if k != "content_sha256"},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")
    payload["content_sha256"] = hashlib.sha256(raw).hexdigest()
    return payload


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    raw_metrics = payload.get("metrics")
    metrics: dict[str, Any] = raw_metrics if isinstance(raw_metrics, dict) else {}
    raw_qwen = metrics.get("qwen")
    qwen: dict[str, Any] = raw_qwen if isinstance(raw_qwen, dict) else {}
    raw_kimi = metrics.get("kimi")
    kimi: dict[str, Any] = raw_kimi if isinstance(raw_kimi, dict) else {}
    lines = [
        "# VLM stamp comparison (tracker 2.2)",
        "",
        f"**status:** `{payload.get('status')}`",
        f"**comparison_status:** `{payload.get('comparison_status')}`",
        f"**qwen_fixture_status:** `{payload.get('qwen_fixture_status')}`",
        f"**kimi_status:** `{payload.get('kimi_status')}`",
        f"**claim_level:** `{payload.get('claim_level')}`",
        "",
        str(payload.get("claim_boundary") or ""),
        "",
        payload.get("skip_reason") or str(payload.get("recommendation") or ""),
        "",
        "| Model | Status | elapsed_ms | regions_read | observations | schema_fail_share |",
        "|---|---|---:|---:|---:|---:|",
        (
            f"| Qwen | {qwen.get('status')} | {qwen.get('elapsed_ms')} | "
            f"{qwen.get('regions_read')} | {qwen.get('observation_count')} | "
            f"{qwen.get('schema_fail_region_share')} |"
        ),
        f"| Kimi | {kimi.get('status')} | — | — | — | — |",
        "",
        f"content_sha256: `{payload.get('content_sha256')}`",
        f"generated_at: `{payload.get('generated_at')}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Open fixture PDF (default: vertical-slice wall-thickness sheet)",
    )
    args = parser.parse_args(argv)
    root = repo_root()
    pdf = args.pdf or (
        root / "samples" / "demo" / "vertical-slice-2026-08-11" / "techlab-a101-wall-thickness.pdf"
    )
    if not pdf.is_file():
        print(json.dumps({"status": "NOT_RUN", "reason": f"pdf missing: {pdf}"}))
        return 2
    payload = run_stamp_comparison(pdf=pdf, sheet_id="TECHLAB-A101")
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    artifacts = args.output or (root / "artifacts" / "vlm-comparison.json")
    evidence = root / "docs" / "evidence" / "vlm-comparison-2026-08.json"
    artifacts.parent.mkdir(parents=True, exist_ok=True)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    artifacts.write_text(text, encoding="utf-8")
    evidence.write_text(text, encoding="utf-8")
    _write_markdown(payload, root / "docs" / "evidence" / "vlm-comparison-2026-08.md")
    print(text, end="")
    status = str(payload.get("status") or "")
    if status in {"LIVE", "SKIPPED", "NOT_RUN", "GATE_REFUSED"}:
        return 0
    if status in {"BLOCKED_BY_GATE", "BLOCKED_BY_SIGNOFF"}:
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
