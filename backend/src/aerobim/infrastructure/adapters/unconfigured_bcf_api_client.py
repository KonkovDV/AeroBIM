"""No-op BCF API client used when remote hub settings are absent."""

from __future__ import annotations

from aerobim.domain.bcf_api import BcfApiPushResult
from aerobim.domain.models import ValidationReport


class UnconfiguredBcfApiClient:
    def push_report_topics(
        self,
        report: ValidationReport,
        *,
        project_id: str,
    ) -> BcfApiPushResult:
        del report, project_id
        raise RuntimeError(
            "BCF API client is not configured. Set AEROBIM_BCF_API_BASE_URL and "
            "AEROBIM_BCF_API_TOKEN (OpenCDE Bearer access token)."
        )
