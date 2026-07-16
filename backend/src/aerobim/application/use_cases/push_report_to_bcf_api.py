"""Push a persisted validation report to a remote BCF API 3.0 hub."""

from __future__ import annotations

from aerobim.domain.bcf_api import BcfApiPushResult
from aerobim.domain.ports import AuditReportStore, BcfApiClient


class PushReportToBcfApiUseCase:
    def __init__(
        self,
        audit_report_store: AuditReportStore,
        bcf_api_client: BcfApiClient,
    ) -> None:
        self._audit_report_store = audit_report_store
        self._bcf_api_client = bcf_api_client

    def execute(self, report_id: str, *, project_id: str) -> BcfApiPushResult:
        report = self._audit_report_store.get(report_id)
        if report is None:
            raise LookupError(f"Report {report_id} not found")
        return self._bcf_api_client.push_report_topics(report, project_id=project_id)
