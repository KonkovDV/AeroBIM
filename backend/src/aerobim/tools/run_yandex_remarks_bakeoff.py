"""Yandex AI Studio remarks bake-off (Sprint 2 Block 5).

Same findings, same prompt, temperature 0, thinking off.
Measures schema-pass, draft length, latency p95, rough RUB/remark.
Does NOT score remark quality without blind expert review.

claim_level=synthetic_only. Never closes RT-001.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings, assert_llm_base_host_allowed
from aerobim.domain.advisory_remark_compose import build_remark_llm_request
from aerobim.domain.llm_token_budget import LlmTokenBudget
from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider

# Candidate short names → Studio model path suffix (folder-prefixed at runtime).
_CANDIDATES = (
    "qwen3.6-35b-a3b",
    "gemma-3-27b-it",
    "deepseek-v4-flash",
    "yandexgpt-5-lite",
    "gpt-oss-120b",
)

# Rough published Studio list prices (RUB / 1K tokens) — update from console if drift.
# Honesty: used only for order-of-magnitude bake-off, not billing SSOT.
_DEFAULT_RUB_PER_1K = {
    "input": 0.20,
    "output": 0.40,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _p95(samples: list[float]) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    idx = max(0, min(len(ordered) - 1, int(0.95 * (len(ordered) - 1) + 0.5)))
    return ordered[idx]


def _load_cases(path: Path, *, limit: int) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise ValueError("cases array required")
    out = [c for c in cases if isinstance(c, dict)]
    return out[: max(1, limit)]


def _findings_from_case(case: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_ctx = case.get("input_context")
    ctx: dict[str, Any] = raw_ctx if isinstance(raw_ctx, dict) else {}
    raw = ctx.get("deterministic_findings") or []
    if not isinstance(raw, list):
        return ()
    return tuple(f for f in raw if isinstance(f, dict))


def _estimate_rub(usage: dict[str, Any] | None) -> float | None:
    if not isinstance(usage, dict):
        return None
    prompt = float(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    completion = float(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return round(
        prompt / 1000.0 * _DEFAULT_RUB_PER_1K["input"]
        + completion / 1000.0 * _DEFAULT_RUB_PER_1K["output"],
        4,
    )


def _provider_for_model(settings: Settings, model_short: str) -> OpenAICompatLlmProvider:
    folder = (settings.llm_folder_id or "").strip()
    model = model_short
    if folder and not model_short.startswith("gpt://"):
        model = f"gpt://{folder}/{model_short}"
    extra: dict[str, str] = {}
    if folder:
        extra["x-folder-id"] = folder
    extra["x-data-logging-enabled"] = "false"
    base = (settings.llm_base_url or "https://llm.api.cloud.yandex.net/v1").rstrip("/")
    assert_llm_base_host_allowed(base, frozenset(settings.llm_allowed_hosts))
    return OpenAICompatLlmProvider(
        base_url=base,
        model=model,
        api_key=settings.llm_api_key,
        provider="yandex-ai-studio",
        folder_id=folder or None,
        temperature=0.0,
        seed=0,
        send_seed=settings.llm_send_seed,
        timeout_seconds=min(60.0, float(settings.llm_timeout_seconds or 60.0)),
        budget=LlmTokenBudget(
            max_tokens_per_call=settings.llm_max_tokens_per_call or 4096,
            max_tokens_per_run=50_000,
            max_tokens_per_day=200_000,
        ),
        max_completion_tokens=min(256, int(settings.llm_max_completion_tokens or 256)),
        allowed_hosts=frozenset(settings.llm_allowed_hosts),
        extra_headers=extra,
        auth_scheme=settings.llm_auth_scheme or "Api-Key",
        response_schema_mode="json_object",
        disable_thinking=True,
        max_concurrent=1,
        retries_429=2,
    )


def run_bakeoff(
    *,
    cases: list[dict[str, Any]],
    models: list[str],
    settings: Settings,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for model_short in models:
        try:
            provider = _provider_for_model(settings, model_short)
        except Exception as exc:
            rows.append(
                {
                    "model": model_short,
                    "status": "SKIP",
                    "reason": f"provider_init_failed: {exc}",
                }
            )
            continue
        latencies: list[float] = []
        schema_ok = 0
        drafts = 0
        costs: list[float] = []
        errors = 0
        for case in cases:
            findings = _findings_from_case(case)
            req = build_remark_llm_request(
                request_id=f"bakeoff-{model_short}-{case.get('case_id')}",
                findings=findings,
                locale="ru",
                allow_customer_data=False,
                allow_synthetic_public=True,
            )
            started = time.perf_counter()
            try:
                resp = provider.generate(req)
                elapsed = time.perf_counter() - started
                latencies.append(elapsed)
                if resp.schema_valid:
                    schema_ok += 1
                if resp.remark_draft:
                    drafts += 1
                rub = _estimate_rub(resp.usage if isinstance(resp.usage, dict) else None)
                if rub is not None:
                    costs.append(rub)
            except Exception as exc:
                errors += 1
                latencies.append(time.perf_counter() - started)
                rows.append(
                    {
                        "model": model_short,
                        "case_id": case.get("case_id"),
                        "status": "ERROR",
                        "detail": str(exc)[:200],
                    }
                )
        n = len(cases)
        rows.append(
            {
                "model": model_short,
                "status": "OK" if errors < n else "FAILED",
                "n_cases": n,
                "schema_pass_rate": round(schema_ok / n, 4) if n else None,
                "draft_present_rate": round(drafts / n, 4) if n else None,
                "latency_mean_s": round(statistics.mean(latencies), 4) if latencies else None,
                "latency_p95_s": round(_p95(latencies) or 0.0, 4) if latencies else None,
                "rub_per_remark_mean": round(statistics.mean(costs), 4) if costs else None,
                "errors": errors,
                "note": "Quality not scored — no blind expert review",
            }
        )
    return {
        "artifact_type": "yandex_remarks_model_bakeoff",
        "schema_version": "1.0.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "claim_level": "synthetic_only",
        "closes_rt001": False,
        "protocol": {
            "temperature": 0.0,
            "thinking": "disabled",
            "same_prompt": True,
            "same_findings": True,
            "provider": "yandex-ai-studio",
        },
        "pricing_note": (
            "RUB estimates use provisional Studio rates in tool constants; "
            "reconcile against console billing before commercial claims."
        ),
        "models": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=None,
        help="Default: samples/benchmarks/llm-advisory/sprint-2-1-cases.json",
    )
    parser.add_argument("--limit-cases", type=int, default=5)
    parser.add_argument(
        "--models",
        default=",".join(_CANDIDATES),
        help="Comma-separated Studio model short names",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    repo = _repo_root()
    day = datetime.now(tz=UTC).date().isoformat()
    out = args.output or (repo / "docs" / "evidence" / f"yandex-remarks-model-bakeoff-{day}.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    key = (os.getenv("AEROBIM_LLM_API_KEY") or "").strip()
    if not key:
        payload = {
            "artifact_type": "yandex_remarks_model_bakeoff",
            "schema_version": "1.0.0",
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "claim_level": "synthetic_only",
            "closes_rt001": False,
            "status": "NOT_RUN",
            "reason": "AEROBIM_LLM_API_KEY not set in this environment",
            "candidates": list(_CANDIDATES),
            "budget_note": (
                "Live bake-off deferred; mock compare remains "
                "artifacts/sprint-2-1/llm-comparison.json"
            ),
        }
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md = out.with_suffix(".md")
        md.write_text(
            "# Yandex remarks bake-off\n\n**Status:** NOT_RUN — missing `AEROBIM_LLM_API_KEY`.\n",
            encoding="utf-8",
        )
        print(json.dumps({"output": str(out), "status": "NOT_RUN"}, indent=2))
        return 0

    settings = Settings.from_env()
    cases_path = args.cases or (
        repo / "samples" / "benchmarks" / "llm-advisory" / "sprint-2-1-cases.json"
    )
    cases = _load_cases(cases_path, limit=args.limit_cases)
    models = [m.strip() for m in str(args.models).split(",") if m.strip()]
    report = run_bakeoff(cases=cases, models=models, settings=settings)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Yandex remarks model bake-off",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- claim_level: `{report['claim_level']}`",
        "",
        "| model | status | schema_pass | p95_s | RUB/remark |",
        "|---|---|---:|---:|---:|",
    ]
    for row in report.get("models") or []:
        if "schema_pass_rate" not in row:
            lines.append(f"| {row.get('model')} | {row.get('status')} | — | — | — |")
            continue
        lines.append(
            f"| {row.get('model')} | {row.get('status')} | {row.get('schema_pass_rate')} | "
            f"{row.get('latency_p95_s')} | {row.get('rub_per_remark_mean')} |"
        )
    lines.extend(
        [
            "",
            "Quality not scored (no blind expert). Synthetic findings only.",
            "",
        ]
    )
    out.with_suffix(".md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(out), "status": "RAN"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
