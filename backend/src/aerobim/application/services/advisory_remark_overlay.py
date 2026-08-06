"""Overlay LLM advisory remark drafts onto deterministic findings (verdict-neutral).

Wired into Analyze after template remarks. Never mutates severity / origin /
``summary.passed``. Unavailable model → capability SKIPPED (not FAILED).

Parallel fan-out uses ``max_workers`` (default from ``AEROBIM_LLM_MAX_CONCURRENT``,
capped at 10 cloud quota). Sequential when ``max_workers<=1``.
"""

from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace

from aerobim.domain.advisory_remark_compose import (
    compose_remark,
    finding_payload_from_issue,
)
from aerobim.domain.llm_advisory import DisabledLlmProvider, LlmProvider
from aerobim.domain.models import CapabilityState, CapabilityStatus, ValidationIssue

# Default cap (~14k tok at ~440/finding). Override via AEROBIM_LLM_ADVISORY_MAX_ISSUES.
_DEFAULT_MAX_ISSUES = 32
_CLOUD_CONCURRENCY_HARD_CAP = 10

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
    max_workers: int = 1,
    allow_synthetic_public: bool = False,
) -> tuple[tuple[ValidationIssue, ...], CapabilityStatus]:
    """Replace template remarks with AI drafts when compose succeeds.

    Issues with ``origin=="advisory"`` are left unchanged (engine owns verdict text).
    ``allow_synthetic_public`` must be True only after HybridRouteGate classifies a
    trusted public corpus path (``/samples/`` or ``/fixtures/``).
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
    workers = max(1, min(int(max_workers), _CLOUD_CONCURRENCY_HARD_CAP))

    # Preserve input order: index → issue; only eligible indices are composed.
    eligible: list[tuple[int, ValidationIssue]] = []
    for index, issue in enumerate(issues):
        if issue.origin == "advisory":
            continue
        if len(eligible) >= cap:
            break
        eligible.append((index, issue))

    drafts: dict[int, ValidationIssue] = {}
    last_skip_reason: str | None = None
    composed = 0
    attempted = len(eligible)

    def _compose_one(
        index: int, issue: ValidationIssue
    ) -> tuple[int, ValidationIssue | None, str | None]:
        result = compose_remark(
            findings=(finding_payload_from_issue(issue),),
            locale=locale_norm,
            request_id=f"{request_id}:remark:{index + 1}",
            provider=provider,
            allow_customer_data=False,
            allow_synthetic_public=allow_synthetic_public,
        )
        if result.status == "OK" and result.remark is not None:
            return index, replace(issue, remark=result.remark), None
        return index, None, result.reason or "model_unavailable"

    if workers <= 1 or attempted <= 1:
        for index, issue in eligible:
            idx, drafted, reason = _compose_one(index, issue)
            if drafted is not None:
                drafts[idx] = drafted
                composed += 1
            elif reason:
                last_skip_reason = reason
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_compose_one, index, issue) for index, issue in eligible]
            for future in as_completed(futures):
                idx, drafted, reason = future.result()
                if drafted is not None:
                    drafts[idx] = drafted
                    composed += 1
                elif reason:
                    last_skip_reason = reason

    enriched = tuple(drafts.get(i, issue) for i, issue in enumerate(issues))

    if composed > 0:
        return (
            enriched,
            CapabilityStatus(
                CapabilityState.OK,
                (
                    f"advisory drafts attached ({composed}/{attempted} of "
                    f"{total_findings} findings, cap={cap}, workers={workers}); "
                    f"{_LLM_ADVISORY_CLAIM}"
                ),
            ),
        )
    reason = last_skip_reason or "model_unavailable"
    return (
        enriched,
        CapabilityStatus(
            CapabilityState.SKIPPED,
            (
                f"llm advisory skipped ({reason}; 0/{attempted} of "
                f"{total_findings} findings, cap={cap}, workers={workers}); "
                f"{_LLM_ADVISORY_CLAIM}"
            ),
        ),
    )


__all__ = ["overlay_llm_remarks", "_DEFAULT_MAX_ISSUES"]
