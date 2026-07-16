"""Shared report-list filtering for filesystem / in-memory stores."""

from __future__ import annotations

from aerobim.domain.models import ReportListFilters, ReportSummaryEntry


def apply_report_list_filters(
    entries: list[ReportSummaryEntry],
    filters: ReportListFilters | None,
) -> list[ReportSummaryEntry]:
    if filters is None:
        return entries
    result = entries
    if filters.project:
        needle = filters.project.strip().lower()
        result = [e for e in result if needle in (e.project_name or "").lower()]
    if filters.discipline:
        needle = filters.discipline.strip().lower()
        result = [e for e in result if needle in (e.discipline or "").lower()]
    if filters.passed is not None:
        result = [e for e in result if e.passed is filters.passed]
    return result
