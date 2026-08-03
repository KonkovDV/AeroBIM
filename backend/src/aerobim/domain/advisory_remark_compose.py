"""Advisory remark compose from deterministic findings (scenario 5.1).

Model sees only structured finding fields — never IFC/drawing/calculation bytes.
Cannot invent findings; verdict_impact is structurally none.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from aerobim.domain.llm_advisory import LlmDataPolicy, LlmProvider, LlmRequest, LlmResponse
from aerobim.domain.models import GeneratedRemark, ValidationIssue

PROMPT_VERSION = "advisory-remark-compose/v1"
CLAIM_BOUNDARY = (
    "Advisory remark draft only. ai_generated=true; expert confirmation required. "
    "Never sets summary.passed. Not product accuracy. Not Qwen 3.8 product claim."
)

ComposeStatus = Literal["OK", "SKIPPED"]


@dataclass(frozen=True)
class RemarkComposeResult:
    """Verdict-neutral compose outcome (CLI + Analyze overlay share this)."""

    status: ComposeStatus
    reason: str | None = None
    remark: GeneratedRemark | None = None
    response: LlmResponse | None = None
    uncertainties: tuple[str, ...] = ()
    provider: str | None = None
    model: str | None = None
    usage: dict[str, Any] | None = None

REMARK_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "locale": {"type": "string", "enum": ["ru", "en"]},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "body", "locale", "evidence_refs"],
}


def finding_payload_from_issue(issue: ValidationIssue) -> dict[str, Any]:
    """Strip to fields safe for local advisory compose (no file bytes)."""

    return {
        "finding_id": issue.finding_id,
        "rule_id": issue.rule_id,
        "category": issue.category.value if issue.category else None,
        "severity": issue.severity.value if issue.severity else None,
        "message": issue.message,
        "source_id": issue.source_id,
        "evidence_refs": list(issue.evidence_refs or ()),
        "ifc_entity": issue.ifc_entity,
        "element_guid": issue.element_guid,
        "target_ref": issue.target_ref,
        "property_set": issue.property_set,
        "property_name": issue.property_name,
        "expected_value": issue.expected_value,
        "observed_value": issue.observed_value,
        "unit": issue.unit,
        "priority": issue.priority,
    }


def build_remark_llm_request(
    *,
    request_id: str,
    findings: tuple[dict[str, Any], ...],
    locale: str = "ru",
    allow_customer_data: bool = False,
) -> LlmRequest:
    locale_norm = "en" if (locale or "ru").strip().lower().startswith("en") else "ru"
    evidence: list[str] = []
    for finding in findings:
        refs = finding.get("evidence_refs") or ()
        if isinstance(refs, (list, tuple)):
            evidence.extend(str(item) for item in refs)
        fid = finding.get("finding_id")
        if fid:
            evidence.append(str(fid))
    return LlmRequest(
        request_id=request_id,
        source_refs=tuple(str(item.get("source_id")) for item in findings if item.get("source_id")),
        evidence_refs=tuple(dict.fromkeys(evidence)),
        deterministic_findings=findings,
        requirements=(
            f"Compose a professional {locale_norm} engineering remark for the given "
            "deterministic findings only. Return JSON matching the schema. "
            "Do not invent findings, GUIDS, or norm citations. "
            "Do not claim accuracy >90%, DWG-ready, CDE interoperable, or expert replacement.",
            f"prompt_version={PROMPT_VERSION}",
            f"locale={locale_norm}",
        ),
        allowed_task="compose_or_rank_advisory_remark",
        data_policy=LlmDataPolicy(
            allow_customer_data=allow_customer_data,
            allow_synthetic_public=True,
            training_use_forbidden=True,
            retention_unknown=False,
            profile="local_open_weight_advisory",
        ),
    )


def parse_remark_response(
    response: LlmResponse,
    *,
    locale: str,
    fallback_evidence: tuple[str, ...],
) -> GeneratedRemark:
    """Parse model draft into GeneratedRemark; fail closed to empty ai draft markers."""

    title = ""
    body = (response.remark_draft or "").strip()
    if response.schema_valid and body.startswith("{"):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            title = str(payload.get("title") or "").strip()
            body = str(payload.get("body") or "").strip()
            refs = payload.get("evidence_refs")
            if isinstance(refs, list) and refs:
                fallback_evidence = tuple(str(item) for item in refs)
    if not title:
        title = "Advisory remark" if locale.startswith("en") else "Черновик замечания"
    if not body:
        body = response.remark_draft or ""
    return GeneratedRemark(
        title=title,
        body=body,
        ai_generated=True,
        expert_confirmation_required=True,
        prompt_version=PROMPT_VERSION,
        provider=response.provider,
        model=response.model,
        evidence_refs=fallback_evidence or response.evidence_refs,
        claim_boundary=CLAIM_BOUNDARY,
    )


def compose_remark(
    *,
    findings: tuple[dict[str, Any], ...],
    locale: str,
    request_id: str,
    provider: LlmProvider,
    allow_customer_data: bool = False,
) -> RemarkComposeResult:
    """Invoke advisory LLM for remark drafts; never mutates verdict fields.

    Unavailable / disabled / policy / schema failures → ``SKIPPED`` (not FAILED).
    """

    request = build_remark_llm_request(
        request_id=request_id,
        findings=findings,
        locale=locale,
        allow_customer_data=allow_customer_data,
    )
    response = provider.generate(request)
    if response.status == "disabled":
        return RemarkComposeResult(
            status="SKIPPED",
            reason="llm_local_disabled",
            response=response,
            uncertainties=tuple(response.uncertainties),
            provider=response.provider,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
        )
    transport_skip = any(str(u).startswith("transport_error:") for u in response.uncertainties)
    if transport_skip or response.status == "failed":
        reason = "model_unavailable"
        if any(str(u) == "truncated" for u in response.uncertainties):
            reason = "response_truncated"
        elif any(str(u) == "reasoning_only" for u in response.uncertainties):
            reason = "reasoning_only"
        elif any(str(u) == "schema_deviation" for u in response.uncertainties):
            reason = "schema_deviation"
        elif any(str(u).startswith("budget_exceeded") for u in response.uncertainties):
            reason = "budget_exceeded"
        return RemarkComposeResult(
            status="SKIPPED",
            reason=reason,
            response=response,
            uncertainties=tuple(response.uncertainties),
            provider=response.provider,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
        )
    if response.status == "blocked_by_policy":
        reason = "blocked_by_policy"
        if any(str(u).startswith("budget_exceeded") for u in response.uncertainties):
            reason = "budget_exceeded"
        return RemarkComposeResult(
            status="SKIPPED",
            reason=reason,
            response=response,
            uncertainties=tuple(response.uncertainties),
            provider=response.provider,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
        )
    if not response.schema_valid:
        return RemarkComposeResult(
            status="SKIPPED",
            reason="schema_deviation",
            response=response,
            uncertainties=tuple(response.uncertainties),
            provider=response.provider,
            model=response.model,
            usage=dict(response.usage) if response.usage else None,
        )
    remark = parse_remark_response(
        response,
        locale=locale,
        fallback_evidence=request.evidence_refs,
    )
    return RemarkComposeResult(
        status="OK",
        remark=remark,
        response=response,
        uncertainties=tuple(response.uncertainties),
        provider=response.provider,
        model=response.model,
        usage=dict(response.usage) if response.usage else None,
    )


__all__ = [
    "CLAIM_BOUNDARY",
    "PROMPT_VERSION",
    "REMARK_JSON_SCHEMA",
    "RemarkComposeResult",
    "build_remark_llm_request",
    "compose_remark",
    "finding_payload_from_issue",
    "parse_remark_response",
]
