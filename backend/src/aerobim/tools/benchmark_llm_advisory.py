"""Mock-based LLM advisory comparison (Kimi/Qwen/Gemma) — no network, no secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from aerobim.domain.llm_advisory import LlmDataPolicy, LlmRequest, MockLlmProvider


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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
        context = case.get("input_context") if isinstance(case.get("input_context"), dict) else {}
        policy = LlmDataPolicy(
            allow_customer_data=False,
            allow_synthetic_public=True,
            retention_unknown=True,
        )
        request = LlmRequest(
            request_id=f"s21-{case_id}",
            evidence_refs=tuple(str(x) for x in (context.get("evidence_refs") or [])),
            deterministic_findings=tuple(
                item for item in (context.get("deterministic_findings") or []) if isinstance(item, dict)
            ),
            requirements=tuple(str(x) for x in (context.get("requirements") or [])),
            data_policy=policy,
        )
        for provider in providers:
            response = provider.generate(request)
            rows.append(
                {
                    "case_id": case_id,
                    "provider": response.provider,
                    "model": response.model,
                    "status": response.status,
                    "schema_valid": response.schema_valid,
                    "unsupported_claims": list(response.unsupported_claims),
                    "evidence_refs": list(response.evidence_refs),
                    "remark_preview": response.remark_draft[:120],
                }
            )
    return {
        "artifact_type": "sprint_2_1_llm_advisory_comparison",
        "schema_version": "1.0.0",
        "claim_level": "synthetic_only",
        "customer_evidence": false_literal(),
        "warning": (
            "Mock comparison only. Not product accuracy. No cloud API calls. "
            "No customer data egress."
        ),
        "rows": rows,
    }


def false_literal() -> bool:
    return False


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
        default=_repo_root() / "artifacts" / "sprint-2-1" / "llm-comparison.json",
    )
    args = parser.parse_args(argv)
    report = run_cases(args.cases.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "rows": len(report["rows"]), "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
