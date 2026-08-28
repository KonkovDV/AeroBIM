"""Template + LLM remark overlay extracted from AnalyzeProjectPackageUseCase."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from aerobim.domain.finding_gate import stamp_finding_gate
from aerobim.domain.llm_advisory import LlmProvider
from aerobim.domain.models import CapabilityStatus, ValidationIssue
from aerobim.domain.ports import RemarkGenerator


class RemarkEnricher:
    def __init__(
        self,
        *,
        remark_generator: RemarkGenerator,
        llm_advisory_provider: LlmProvider | None = None,
        remark_locale: str = "ru",
        llm_advisory_max_issues: int = 32,
        llm_max_concurrent: int = 4,
    ) -> None:
        self._remark_generator = remark_generator
        self._llm_advisory_provider = llm_advisory_provider
        self._remark_locale = remark_locale
        self._llm_advisory_max_issues = llm_advisory_max_issues
        self._llm_max_concurrent = llm_max_concurrent

    def attach_remarks(self, issues: Iterable[ValidationIssue]) -> list[ValidationIssue]:
        enriched: list[ValidationIssue] = []
        for issue in issues:
            remark = self._remark_generator.generate(issue)
            stamped = stamp_finding_gate(issue)
            enriched.append(replace(stamped, remark=remark))
        return enriched

    def overlay_llm_remarks(
        self,
        issues: Iterable[ValidationIssue],
        *,
        request_id: str,
        allow_synthetic_public: bool = False,
    ) -> tuple[tuple[ValidationIssue, ...], CapabilityStatus]:
        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks

        return overlay_llm_remarks(
            tuple(issues),
            provider=self._llm_advisory_provider,
            request_id=request_id,
            locale=self._remark_locale,
            max_issues=self._llm_advisory_max_issues,
            max_workers=self._llm_max_concurrent,
            allow_synthetic_public=allow_synthetic_public,
        )
