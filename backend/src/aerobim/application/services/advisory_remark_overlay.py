"""Overlay LLM advisory remark drafts onto deterministic findings (verdict-neutral).

Wired into Analyze after template remarks. Never mutates severity / origin /
``summary.passed``. Unavailable model → capability SKIPPED (not FAILED).

Call path is sequential today; ``AEROBIM_LLM_MAX_CONCURRENT`` / adapter
``BoundedSemaphore`` is unused until September parallel fan-out.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from aerobim.domain.advisory_remark_compose import (
    compose_remark,
    finding_payload_from_issue,
)
from aerobim.domain.llm_advisory import DisabledLlmProvider, LlmProvider
from aerobim.domain.models import CapabilityState, CapabilityStatus, ValidationIssue

# Default cap (~14k tok at ~440/finding). Override via AEROBIM_LLM_ADVISORY_MAX_ISSUES.
_DEFAULT_MAX_ISSUES = 32

_LLM_ADVISORY_CLAIM = (
    "Advisory remark drafts only; never sets summary.passed; "
    "ai_generated requires expert confirmation"
)


def overlay_llm_remarks(
    issues: Sequence[ValidationIssue],
    *,
    provider: LlmProvider | None,
    request_id: str,
    locale: str = "ru",
    max_issues: int = _DEFAULT_MAX_ISSUES,
) -> tuple[tuple[ValidationIssue, ...], CapabilityStatus]:
    """Replace template remarks with AI drafts when compose succeeds.

    Issues with ``origin=="advisory"`` are left unchanged (engine owns verdict text).
    """

    total_findings = len(issues)
    if provider is None or isinstance(provider, DisabledLlmProvider):
        return (
            tuple(issues),
            CapabilityStatus(
                CapabilityState.SKIPPED,
                f"llm advisory not configured; {_LLM_ADVISORY_CLAIM}",
            ),
        )

    locale_norm = "en" if (locale or "ru").strip().lower().startswith("en") else "ru"
    cap = max(0, int(max_issues))
    enriched: list[ValidationIssue] = []
    composed = 0
    attempted = 0
    last_skip_reason: str | None = None

    for issue in issues:
        if issue.origin == "advisory" or attempted >= cap or composed >= cap:
            enriched.append(issue)
            continue

        attempted += 1
        result = compose_remark(
            findings=(finding_payload_from_issue(issue),),
            locale=locale_norm,
            request_id=f"{request_id}:remark:{attempted}",
            provider=provider,
            allow_customer_data=False,
        )
        if result.status == "OK" and result.remark is not None:
            composed += 1
            enriched.append(replace(issue, remark=result.remark))
        else:
            last_skip_reason = result.reason or "model_unavailable"
            enriched.append(issue)

    if composed > 0:
        return (
            tuple(enriched),
            CapabilityStatus(
                CapabilityState.OK,
                (
                    f"advisory drafts attached ({composed}/{attempted} of "
                    f"{total_findings} findings, cap={cap}); {_LLM_ADVISORY_CLAIM}"
                ),
            ),
        )
    reason = last_skip_reason or "model_unavailable"
    return (
        tuple(enriched),
        CapabilityStatus(
            CapabilityState.SKIPPED,
            (
                f"llm advisory skipped ({reason}; 0/{attempted} of "
                f"{total_findings} findings, cap={cap}); {_LLM_ADVISORY_CLAIM}"
            ),
        ),
    )


__all__ = ["overlay_llm_remarks", "_DEFAULT_MAX_ISSUES"]
