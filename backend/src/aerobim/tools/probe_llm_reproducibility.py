"""Probe OpenAI-compat advisory LLM reproducibility (temperature=0 hash compare).

Honesty: does NOT declare ``reproducible=true`` without two matching runs.
Stores baseline + compare artifacts under ``artifacts/llm-repro/``.
Never puts results into customer evidence bundle automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.advisory_remark_compose import PROMPT_VERSION, build_remark_llm_request
from aerobim.infrastructure.di.bootstrap import bootstrap_container

CLAIM_BOUNDARY = (
    "Reproducibility probe only. Splits P1 (deterministic_intrasession) vs P2 "
    "(stable_across_time). Report verdict reproducibility is independent (ADR-001). "
    "partial ≠ product evidence. Never summary.passed."
)


def _content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_once(
    provider: Any,
    findings: tuple[dict[str, Any], ...],
    request_id: str,
) -> dict[str, Any]:
    request = build_remark_llm_request(
        request_id=request_id,
        findings=findings,
        locale="ru",
        allow_customer_data=False,
        allow_synthetic_public=True,
    )
    response = provider.generate(request)
    draft = response.remark_draft or ""
    return {
        "status": response.status,
        "schema_valid": response.schema_valid,
        "provider": response.provider,
        "model": response.model,
        "usage": response.usage,
        "uncertainties": list(response.uncertainties),
        "draft_sha256": _content_sha256(draft),
        "draft_len": len(draft),
    }


def compare_runs(
    baseline: dict[str, Any],
    current: dict[str, Any],
    *,
    mode: str = "intrasession",
) -> dict[str, Any]:
    """Compare two probe runs.

    ``mode=intrasession`` → P₁ (same session repeats).
    ``mode=across_time`` → P₂ (Δ≈14d on pinned URI).
    Legacy ``reproducible`` is true only when the active mode's property holds.
    """

    match = (
        baseline.get("status") == "advisory"
        and current.get("status") == "advisory"
        and baseline.get("draft_sha256")
        and baseline.get("draft_sha256") == current.get("draft_sha256")
    )
    if match:
        status = "reproducible"
    elif baseline.get("draft_sha256") and current.get("draft_sha256"):
        status = "partial"
    else:
        status = "failed"
    mode_norm = (mode or "intrasession").strip().lower()
    p1 = match if mode_norm == "intrasession" else None
    p2 = match if mode_norm == "across_time" else None
    return {
        "artifact_type": "llm_reproducibility_probe",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "mode": mode_norm,
        "deterministic_intrasession": p1,
        "stable_across_time": p2,
        "reproducible": match,
        "status": status,
        "baseline": baseline,
        "current": current,
        "note": (
            "Keep partial/failed out of customer evidence bundle. "
            "P1 ≠ P2: run intrasession and across_time probes separately. "
            "Report verdict reproducibility does not depend on model determinism (ADR-001)."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings-json", type=Path, required=True)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Prior probe JSON; if omitted, write baseline only (exit 0)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Default: <repo>/artifacts/llm-repro",
    )
    parser.add_argument(
        "--mode",
        choices=("intrasession", "across_time"),
        default="intrasession",
        help="P1 intrasession vs P2 across_time (Δ≈14d)",
    )
    args = parser.parse_args(argv)

    payload = json.loads(args.findings_json.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        findings = tuple(item for item in payload if isinstance(item, dict))
    else:
        raw = payload.get("findings") or []
        findings = tuple(item for item in raw if isinstance(item, dict))
    if not findings:
        print("no findings", file=sys.stderr)
        return 1

    settings = Settings.from_env()
    if not settings.llm_local_ready():
        print(json.dumps({"status": "SKIPPED", "reason": "llm_local_disabled"}, indent=2))
        return 2

    container = bootstrap_container(settings)
    provider = container.resolve(Tokens.LLM_ADVISORY_PROVIDER)
    current = _run_once(provider, findings, "llm-repro-current")

    repo = Path(__file__).resolve().parents[4]
    out_dir = args.out_dir or (repo / "artifacts" / "llm-repro")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.baseline is None:
        baseline_path = out_dir / "baseline.json"
        record = {
            "artifact_type": "llm_reproducibility_baseline",
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "prompt_version": PROMPT_VERSION,
            "claim_boundary": CLAIM_BOUNDARY,
            "model": settings.llm_model,
            "model_sha256": settings.llm_model_sha256,
            "provider": settings.llm_provider,
            "temperature": 0.0,
            "run": current,
            "reproducible": False,
            "status": "baseline_only",
            "note": "Compare later with --baseline pointing at this file.",
        }
        baseline_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0 if current.get("status") == "advisory" else 1

    baseline_doc = json.loads(args.baseline.read_text(encoding="utf-8"))
    if isinstance(baseline_doc.get("run"), dict):
        baseline_run = baseline_doc["run"]
    else:
        baseline_run = baseline_doc
    report = compare_runs(baseline_run, current, mode=args.mode)
    report["model"] = settings.llm_model
    report["model_sha256"] = settings.llm_model_sha256
    out_path = out_dir / "compare.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["reproducible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
