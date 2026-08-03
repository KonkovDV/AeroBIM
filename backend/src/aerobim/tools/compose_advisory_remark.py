"""Compose advisory RU/EN remarks from deterministic findings (scenario 5.1).

Opt-in local LLM path — never touches Analyze verdict / summary.passed.
When LLM is disabled, exits 2 (skip). Schema failures exit 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.advisory_remark_compose import (
    CLAIM_BOUNDARY,
    PROMPT_VERSION,
    build_remark_llm_request,
    parse_remark_response,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container


def compose_from_findings(
    *,
    findings: tuple[dict[str, Any], ...],
    locale: str,
    request_id: str,
    provider: Any,
) -> dict[str, Any]:
    request = build_remark_llm_request(
        request_id=request_id,
        findings=findings,
        locale=locale,
        allow_customer_data=False,
    )
    response = provider.generate(request)
    if response.status == "disabled":
        return {
            "status": "SKIPPED",
            "reason": "llm_local_disabled",
            "claim_boundary": CLAIM_BOUNDARY,
            "prompt_version": PROMPT_VERSION,
        }
    if response.status in {"failed", "blocked_by_policy"} or not response.schema_valid:
        return {
            "status": "FAILED",
            "reason": response.status,
            "uncertainties": list(response.uncertainties),
            "claim_boundary": CLAIM_BOUNDARY,
            "prompt_version": PROMPT_VERSION,
            "provider": response.provider,
            "model": response.model,
            "usage": response.usage,
        }
    remark = parse_remark_response(
        response,
        locale=locale,
        fallback_evidence=request.evidence_refs,
    )
    return {
        "status": "OK",
        "claim_boundary": CLAIM_BOUNDARY,
        "prompt_version": PROMPT_VERSION,
        "verdict_impact": "none",
        "ai_generated": True,
        "expert_confirmation_required": True,
        "provider": response.provider,
        "model": response.model,
        "usage": response.usage,
        "remark": asdict(remark),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--findings-json",
        type=Path,
        required=True,
        help="JSON file: {findings:[{...}]} or a bare findings array",
    )
    parser.add_argument("--locale", default="ru", choices=("ru", "en"))
    parser.add_argument("--request-id", default="advisory-remark-compose")
    args = parser.parse_args(argv)

    payload = json.loads(args.findings_json.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        findings = tuple(item for item in payload if isinstance(item, dict))
    elif isinstance(payload, dict):
        raw = payload.get("findings") or payload.get("deterministic_findings") or []
        findings = tuple(item for item in raw if isinstance(item, dict))
    else:
        print("findings JSON must be an object or array", file=sys.stderr)
        return 1
    if not findings:
        print("no findings provided", file=sys.stderr)
        return 1

    settings = Settings.from_env()
    container = bootstrap_container(settings)
    provider = container.resolve(Tokens.LLM_ADVISORY_PROVIDER)
    result = compose_from_findings(
        findings=findings,
        locale=args.locale,
        request_id=args.request_id,
        provider=provider,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "SKIPPED":
        return 2
    if result["status"] != "OK":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
