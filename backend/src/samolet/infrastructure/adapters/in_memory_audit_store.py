from __future__ import annotations

from samolet.domain.models import ReportSummaryEntry, ValidationReport


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._reports: dict[str, ValidationReport] = {}

    def save(self, report: ValidationReport) -> str:
        self._reports[report.report_id] = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._reports.get(report_id)

    def list_reports(self) -> list[ReportSummaryEntry]:
        return [
            ReportSummaryEntry(
                report_id=r.report_id,
                request_id=r.request_id,
                created_at=r.created_at,
                passed=r.summary.passed,
                issue_count=r.summary.issue_count,
            )
            for r in self._reports.values()
        ]
