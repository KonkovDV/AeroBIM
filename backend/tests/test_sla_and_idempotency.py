"""SLA stage budgets and job idempotency hardening."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
    SubmitAnalyzeProjectPackageJobUseCase,
)
from aerobim.domain.architecture import DEFAULT_PACKAGE_STAGE_BUDGET, StageBudget
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    JobStatus,
    RequirementSource,
    SourceKind,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


class StageBudgetTests(unittest.TestCase):
    def test_default_budgets_sum_to_thirty(self) -> None:
        self.assertEqual(DEFAULT_PACKAGE_STAGE_BUDGET.total_minutes, 30.0)
        payload = DEFAULT_PACKAGE_STAGE_BUDGET.as_dict()
        self.assertIn("ingestion_minutes", payload)
        self.assertEqual(payload["total_minutes"], 30.0)

    def test_custom_budget_total(self) -> None:
        budget = StageBudget(
            ingestion_minutes=1,
            deterministic_validation_minutes=2,
            ai_advisory_minutes=3,
            evidence_reporting_minutes=4,
        )
        self.assertEqual(budget.total_minutes, 10.0)


class JobIdempotencyTests(unittest.TestCase):
    def _request(self) -> ValidationRequest:
        return ValidationRequest(
            request_id="req-idem-1",
            ifc_path=Path("sample.ifc"),
            requirement_source=RequirementSource(
                text="height = 3 m",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        )

    def test_submit_returns_same_job_for_idempotency_key(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        submit = SubmitAnalyzeProjectPackageJobUseCase(store)
        first = submit.execute(self._request(), idempotency_key="client-key-1")
        second = submit.execute(self._request(), idempotency_key="client-key-1")
        self.assertEqual(first.job_id, second.job_id)
        self.assertEqual(first.idempotency_key, "client-key-1")

    def test_runner_skips_when_job_not_claimable(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job = AnalyzeProjectPackageJob(
            job_id="job-done",
            request_id="req-done",
            status=JobStatus.SUCCEEDED,
            created_at="2026-07-16T00:00:00+00:00",
            report_id="report-1",
            idempotency_key="k",
        )
        store.create(job)
        analyze = MagicMock()
        logger = MagicMock()
        runner = AnalyzeProjectPackageJobRunner(analyze, store, logger)
        runner.run("job-done", self._request())
        analyze.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
