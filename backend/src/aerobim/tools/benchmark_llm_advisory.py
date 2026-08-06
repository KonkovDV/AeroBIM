"""Mock-based LLM advisory comparison (Kimi/Qwen/Gemma) — no network, no secrets.

claim_level=fixture_only/synthetic_only. Never mutates summary.passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from aerobim.domain.llm_advisory import LlmDataPolicy, LlmRequest, MockLlmProvider

CLAIM_LEVEL = "fixture_only"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _agreement_with_deterministic(
    response_status: str,
    findings: list[Any],
) -> dict[str, Any]:
    """Placeholder agreement: mock stays evidence-bounded; never invents findings."""

    if not findings:
        return {
            "status": "no_deterministic_findings",
            "agrees": None,
            "note": "Cannot score agreement without deterministic findings",
        }
    return {
        "status": "mock_evidence_bounded",
        "agrees": response_status in {"advisory", "ok", "success"},
        "deterministic_finding_count": len(findings),
        "note": "Mock agreement placeholder — not product accuracy",
    }


def run_cases(cases_path: Path) -> dict[str, Any]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise ValueError("cases must be an array")

    providers = (
        MockLlmProvider(provider="kimi", model="kimi-mock"),
        MockLlmProvider(provider="qwen", model="qwen-mock"),
        MockLlmProvider(provider="gemma", model="gemma-mock"),
    )
    rows: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("case_id") or "")
        raw_ctx = case.get("input_context")
        context: dict[str, Any] = raw_ctx if isinstance(raw_ctx, dict) else {}
        policy = LlmDataPolicy(
            allow_customer_data=False,
            allow_synthetic_public=True,
            retention_unknown=True,
        )
        findings = context.get("deterministic_findings") or []
        finding_list = [item for item in findings if isinstance(item, dict)]
        request = LlmRequest(
            request_id=f"s21-{case_id}",
            evidence_refs=tuple(str(x) for x in (context.get("evidence_refs") or [])),
            deterministic_findings=tuple(finding_list),
            requirements=tuple(str(x) for x in (context.get("requirements") or [])),
            data_policy=policy,
        )
        for provider in providers:
            started = time.perf_counter()
            response = provider.generate(request)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 3)
            # Mock latency floor for schema completeness (deterministic-ish).
            if latency_ms <= 0:
                latency_ms = 0.001
            json_validity = bool(response.schema_valid)
            rows.append(
                {
                    "case_id": case_id,
                    "provider": response.provider,
                    "model": response.model,
                    "status": response.status,
                    "schema_valid": response.schema_valid,
                    "json_validity": json_validity,
                    "latency_ms": latency_ms,
                    "cost": None,
                    "unsupported_claims": list(response.unsupported_claims),
                    "evidence_refs": list(response.evidence_refs),
                    "remark_preview": response.remark_draft[:120],
                    "agreement_with_deterministic": _agreement_with_deterministic(
                        response.status, finding_list
                    ),
                    "hallucination_placeholder": {
                        "status": "not_scored",
                        "reason": "No human hallucination labels in mock bench",
                    },
                    "error_placeholder": {
                        "error_class": None,
                        "note": "Mock path; live errors only when API keys present",
                    },
                    "affects_summary_passed": False,
                }
            )
    row_hash = _sha256_text(
        json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    return {
        "artifact_type": "sprint_2_llm_advisory_comparison",
        "schema_version": "1.1.0",
        "claim_level": CLAIM_LEVEL,
        "customer_evidence": False,
        "customer_precision_claim_publishable": False,
        "affects_summary_passed": False,
        "reproducibility": {
            "rows_sha256": row_hash,
            "cases_path": str(cases_path).replace("\\", "/"),
            "mode": "mock_no_network",
        },
        "warning": (
            "Mock comparison only. Not product accuracy. No cloud API calls. "
            "No customer data egress. Does not change summary.passed."
        ),
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=_repo_root() / "samples" / "benchmarks" / "llm-advisory" / "sprint-2-1-cases.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_repo_root() / "artifacts" / "sprint-2" / "llm-comparison.json",
    )
    args = parser.parse_args(argv)
    report = run_cases(args.cases.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    summary = {
        "ok": True,
        "rows": len(report["rows"]),
        "output": str(args.output),
        "claim_level": report["claim_level"],
        "affects_summary_passed": report["affects_summary_passed"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
