from __future__ import annotations

from aerobim.application.services.report_list_filters import apply_report_list_filters
from aerobim.domain.models import ReportListFilters, ReportSummaryEntry, ValidationReport


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._reports: dict[str, ValidationReport] = {}

    def save(self, report: ValidationReport) -> str:
        self._reports[report.report_id] = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._reports.get(report_id)

    def list_reports(
        self,
        filters: ReportListFilters | None = None,
    ) -> list[ReportSummaryEntry]:
        entries = [
            ReportSummaryEntry(
                report_id=r.report_id,
                request_id=r.request_id,
                created_at=r.created_at,
                passed=r.summary.passed,
                issue_count=r.summary.issue_count,
                project_name=r.project_name,
                discipline=r.discipline,
            )
            for r in self._reports.values()
        ]
        return apply_report_list_filters(entries, filters)
