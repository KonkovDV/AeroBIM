"""Fault injection: a dead runner does not duplicate a published report."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from aerobim.application.use_cases.analyze_job_recovery import recover_abandoned_jobs
from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
)
from aerobim.domain.models import (
    AnalyzeProjectPackageJob,
    JobStatus,
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


class _Logger:
    def info(self, *_args: object, **_kwargs: object) -> None:
        return None

    def error(self, *_args: object, **_kwargs: object) -> None:
        return None


class _Analyzer:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: ValidationRequest) -> SimpleNamespace:
        self.calls += 1
        return SimpleNamespace(report_id=f"report-{self.calls}", request_id=request.request_id)


def _request() -> ValidationRequest:
    return ValidationRequest(
        request_id="req-1",
        ifc_path=None,
        requirement_source=RequirementSource(text="REQ"),
    )


class AnalyzeJobRecoveryTests(unittest.TestCase):
    def test_expired_lease_reruns_once_and_does_not_duplicate(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore(lease_seconds=120)
        job_id = "c" * 32
        store.create(
            AnalyzeProjectPackageJob(
                job_id=job_id,
                request_id="req-1",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
            )
        )
        claimed = store.mark_running(job_id, owner="dead-worker")
        assert claimed is not None
        later = (datetime.now(tz=UTC) + timedelta(hours=1)).isoformat()
        expired = store.reclaim_stale_running(now_iso=later)
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0].status, JobStatus.FAILED)
        self.assertIsNone(expired[0].report_id)

        analyzer = _Analyzer()
        runner = AnalyzeProjectPackageJobRunner(analyzer, store, _Logger())
        requests = {job_id: _request()}

        first = recover_abandoned_jobs(store, runner, requests)
        self.assertEqual(first, [job_id])
        self.assertEqual(analyzer.calls, 1)
        finished = store.get(job_id)
        assert finished is not None
        self.assertEqual(finished.status, JobStatus.SUCCEEDED)
        self.assertEqual(finished.report_id, "report-1")

        second = recover_abandoned_jobs(store, runner, requests)
        self.assertEqual(second, [])
        self.assertEqual(analyzer.calls, 1)
        again = store.get(job_id)
        assert again is not None
        self.assertEqual(again.report_id, "report-1")

    def test_business_failure_is_not_requeued(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job_id = "d" * 32
        store.create(
            AnalyzeProjectPackageJob(
                job_id=job_id,
                request_id="req-2",
                status=JobStatus.FAILED,
                created_at=datetime.now(tz=UTC).isoformat(),
                error_message="No requirements were extracted",
                retry_count=1,
            )
        )
        self.assertIsNone(store.requeue_failed_without_report(job_id))
        self.assertEqual(store.get(job_id).status, JobStatus.FAILED)  # type: ignore[union-attr]

    def test_restart_snapshot_of_running_job_can_finish_once(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "jobs.json"
            job_id = "e" * 32
            first_store = InMemoryAnalyzeProjectPackageJobStore(snapshot)
            first_store.create(
                AnalyzeProjectPackageJob(
                    job_id=job_id,
                    request_id="req-3",
                    status=JobStatus.QUEUED,
                    created_at=datetime.now(tz=UTC).isoformat(),
                )
            )
            first_store.mark_running(job_id, owner="api-process")

            restarted = InMemoryAnalyzeProjectPackageJobStore(snapshot)
            interrupted = restarted.get(job_id)
            assert interrupted is not None
            self.assertEqual(interrupted.status, JobStatus.FAILED)
            self.assertIn("process restart", interrupted.error_message or "")

            analyzer = _Analyzer()
            runner = AnalyzeProjectPackageJobRunner(analyzer, restarted, _Logger())
            recover_abandoned_jobs(restarted, runner, {job_id: _request()})
            self.assertEqual(analyzer.calls, 1)
            done = restarted.get(job_id)
            assert done is not None
            self.assertEqual(done.status, JobStatus.SUCCEEDED)
            recover_abandoned_jobs(restarted, runner, {job_id: _request()})
            self.assertEqual(analyzer.calls, 1)
