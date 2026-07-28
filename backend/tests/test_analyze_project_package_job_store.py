from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


class AnalyzeProjectPackageJobStoreDurabilityTests(unittest.TestCase):
    def test_store_persists_and_recovers_jobs_from_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "jobs.snapshot.json"
            store = InMemoryAnalyzeProjectPackageJobStore(snapshot_path=snapshot_path)

            job = AnalyzeProjectPackageJob(
                job_id="job-001",
                request_id="req-001",
                status=JobStatus.QUEUED,
                created_at="2026-04-19T00:00:00+00:00",
            )

            store.create(job)
            store.mark_running("job-001")
            store.mark_failed("job-001", "durability test failure")

            recovered_store = InMemoryAnalyzeProjectPackageJobStore(snapshot_path=snapshot_path)
            recovered_job = recovered_store.get("job-001")

            self.assertIsNotNone(recovered_job)
            assert recovered_job is not None
            self.assertEqual(recovered_job.status, JobStatus.FAILED)
            self.assertEqual(recovered_job.error_message, "durability test failure")
            self.assertIsNotNone(recovered_job.started_at)
            self.assertIsNotNone(recovered_job.completed_at)

    def test_store_rejects_invalid_snapshot_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "jobs.snapshot.json"
            snapshot_path.write_text("{ invalid json", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                InMemoryAnalyzeProjectPackageJobStore(snapshot_path=snapshot_path)

    def test_store_rejects_non_list_snapshot_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "jobs.snapshot.json"
            snapshot_path.write_text('{"jobs": []}', encoding="utf-8")

            with self.assertRaises(RuntimeError):
                InMemoryAnalyzeProjectPackageJobStore(snapshot_path=snapshot_path)

    def test_illegal_transition_is_rejected(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        job = AnalyzeProjectPackageJob(
            job_id="job-locked",
            request_id="req-locked",
            status=JobStatus.QUEUED,
            created_at="2026-04-19T00:00:00+00:00",
        )
        store.create(job)
        # Cannot jump QUEUED → SUCCEEDED.
        self.assertIsNone(store.mark_succeeded("job-locked", "report-1"))
        self.assertEqual(store.get("job-locked").status, JobStatus.QUEUED)  # type: ignore[union-attr]

        store.mark_running("job-locked")
        store.mark_succeeded("job-locked", "report-1")
        # Terminal SUCCEEDED cannot move back to RUNNING or FAILED.
        self.assertIsNone(store.mark_running("job-locked"))
        self.assertIsNone(store.mark_failed("job-locked", "nope"))
        recovered = store.get("job-locked")
        assert recovered is not None
        self.assertEqual(recovered.status, JobStatus.SUCCEEDED)
        self.assertEqual(recovered.report_id, "report-1")


class AnalyzeProjectPackageJobIdempotencyTests(unittest.TestCase):
    def _queued(
        self, job_id: str, *, key: str | None = None, tenant: str | None = None
    ) -> AnalyzeProjectPackageJob:
        return AnalyzeProjectPackageJob(
            job_id=job_id,
            request_id=f"req-{job_id}",
            status=JobStatus.QUEUED,
            created_at="2026-04-19T00:00:00+00:00",
            idempotency_key=key,
            tenant_id=tenant,
        )

    def test_idempotency_key_dedup_same_tenant(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        first = store.create(self._queued("job-a", key="k1", tenant="t1"))
        second = store.create(self._queued("job-b", key="k1", tenant="t1"))
        self.assertEqual(first, "job-a")
        self.assertEqual(second, "job-a")  # duplicate resubmit returns the existing job id
        self.assertIsNone(store.get("job-b"))  # the duplicate was never stored

    def test_idempotency_key_is_tenant_scoped(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(self._queued("job-t1", key="k1", tenant="t1"))
        created = store.create(self._queued("job-t2", key="k1", tenant="t2"))
        self.assertEqual(created, "job-t2")  # same key, different tenant -> NOT deduped
        t1 = store.get_by_idempotency_key("k1", tenant_id="t1")
        t2 = store.get_by_idempotency_key("k1", tenant_id="t2")
        assert t1 is not None and t2 is not None
        self.assertEqual(t1.job_id, "job-t1")
        self.assertEqual(t2.job_id, "job-t2")

    def test_cancel_queued_prevents_resurrection(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(self._queued("job-c"))
        cancelled = store.request_cancel("job-c")
        assert cancelled is not None
        self.assertEqual(cancelled.status, JobStatus.CANCELLED)
        # A cancelled job can never be (re)started.
        self.assertIsNone(store.mark_running("job-c"))
        after = store.get("job-c")
        assert after is not None
        self.assertEqual(after.status, JobStatus.CANCELLED)

    def test_running_cancel_request_then_heartbeat_cancels(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(self._queued("job-r"))
        store.mark_running("job-r")
        requested = store.request_cancel("job-r")
        assert requested is not None
        self.assertEqual(requested.status, JobStatus.RUNNING)  # co-operative: still running
        self.assertTrue(requested.cancel_requested)
        beat = store.heartbeat("job-r")
        assert beat is not None
        self.assertEqual(beat.status, JobStatus.CANCELLED)  # honoured on next heartbeat


class AnalyzeProjectPackageJobRunnerCancelTests(unittest.TestCase):
    def test_cancelled_job_is_never_executed_or_succeeded(self) -> None:
        from types import SimpleNamespace

        from aerobim.application.use_cases.analyze_project_package_jobs import (
            AnalyzeProjectPackageJobRunner,
        )

        class _RecordingAnalyze:
            def __init__(self) -> None:
                self.calls = 0

            def execute(self, request: object) -> object:
                self.calls += 1
                return SimpleNamespace(report_id="should-not-happen")

        class _NullLogger:
            def info(self, *args: object, **kwargs: object) -> None: ...
            def error(self, *args: object, **kwargs: object) -> None: ...
            def warning(self, *args: object, **kwargs: object) -> None: ...

        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(
            AnalyzeProjectPackageJob(
                job_id="job-x",
                request_id="req-x",
                status=JobStatus.QUEUED,
                created_at="2026-04-19T00:00:00+00:00",
            )
        )
        store.request_cancel("job-x")  # QUEUED -> CANCELLED before the runner claims it
        analyze = _RecordingAnalyze()
        runner = AnalyzeProjectPackageJobRunner(analyze, store, _NullLogger())
        runner.run("job-x", SimpleNamespace(request_id="req-x"))
        self.assertEqual(analyze.calls, 0)  # cancelled job is never executed
        after = store.get("job-x")
        assert after is not None
        self.assertEqual(after.status, JobStatus.CANCELLED)  # never SUCCEEDED


if __name__ == "__main__":
    unittest.main()
