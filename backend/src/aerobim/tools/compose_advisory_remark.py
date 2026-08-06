"""Compose advisory RU/EN remarks from deterministic findings (scenario 5.1).

Opt-in LLM path — never touches Analyze verdict / summary.passed.
When LLM is disabled, exits 2 (skip). Schema / budget failures exit 1.
Budget counters land in ``audit_event.usage`` (fail-closed caps in the adapter).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.advisory_remark_compose import (
    CLAIM_BOUNDARY,
    PROMPT_VERSION,
    compose_remark,
)
from aerobim.domain.hybrid.audit_event import build_route_audit_event
from aerobim.domain.hybrid.data_classification import DataClassification
from aerobim.domain.hybrid.trust_policy import RouteTarget, decide_route
from aerobim.infrastructure.di.bootstrap import bootstrap_container


def _advisory_audit_event(
    *,
    request_id: str,
    response: Any,
    settings: Settings,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    """Hybrid audit record for remark compose — verdict_impact none."""

    host = urlparse(settings.llm_base_url or "").hostname or ""
    target = (
        RouteTarget.LOCAL if host in {"localhost", "127.0.0.1", "::1", ""} else RouteTarget.PRIVATE
    )
    decision = decide_route(
        classification=DataClassification.INTERNAL,
        target=target,
        tenant_id="advisory-compose",
    )
    usage = response.usage if isinstance(getattr(response, "usage", None), dict) else {}
    event = build_route_audit_event(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(tz=UTC).isoformat(),
        request_id=request_id,
        tenant_id="advisory-compose",
        task_type="compose_advisory_remark",
        decision=decision,
        policy_version="grant-kt2-1.0",
        failure_reason=failure_reason,
        model_provider=getattr(response, "provider", None),
        model_id=getattr(response, "model", None),
        model_snapshot=settings.llm_model_sha256,
        endpoint=host or None,
        usage=usage,
    )
    payload = event.to_audit_dict()
    payload["event_content_hash"] = event.event_content_hash()
    payload["prompt_version"] = PROMPT_VERSION
    return payload


def compose_from_findings(
    *,
    findings: tuple[dict[str, Any], ...],
    locale: str,
    request_id: str,
    provider: Any,
    settings: Settings | None = None,
) -> dict[str, Any]:
    resolved = settings or Settings.from_env()
    result = compose_remark(
        findings=findings,
        locale=locale,
        request_id=request_id,
        provider=provider,
        allow_customer_data=False,
        allow_synthetic_public=True,
    )
    base: dict[str, Any] = {
        "status": result.status,
        "claim_boundary": CLAIM_BOUNDARY,
        "prompt_version": PROMPT_VERSION,
    }
    if result.reason:
        base["reason"] = result.reason
    if result.uncertainties:
        base["uncertainties"] = list(result.uncertainties)
    if result.provider is not None:
        base["provider"] = result.provider
    if result.model is not None:
        base["model"] = result.model
    if result.usage is not None:
        base["usage"] = result.usage
    if result.response is not None:
        base["audit_event"] = _advisory_audit_event(
            request_id=request_id,
            response=result.response,
            settings=resolved,
            failure_reason=result.reason if result.status == "SKIPPED" else None,
        )
    if result.status == "OK" and result.remark is not None:
        base["verdict_impact"] = "none"
        base["ai_generated"] = True
        base["expert_confirmation_required"] = True
        base["remark"] = asdict(result.remark)
    return base


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
        settings=settings,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "SKIPPED":
        return 2
    if result["status"] != "OK":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
