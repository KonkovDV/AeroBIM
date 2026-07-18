"""Phase 6 jobs: lease reclaim, cancel, dead-letter after retries."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus
from aerobim.infrastructure.adapters.in_memory_analyze_project_package_job_store import (
    InMemoryAnalyzeProjectPackageJobStore,
)


class Phase6JobLeaseTests(unittest.TestCase):
    def test_cancel_queued_job(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(
            AnalyzeProjectPackageJob(
                job_id="a" * 32,
                request_id="r1",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
            )
        )
        cancelled = store.request_cancel("a" * 32)
        assert cancelled is not None
        self.assertEqual(cancelled.status, JobStatus.CANCELLED)

    def test_cancel_running_sets_flag_then_heartbeat_cancels(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore()
        store.create(
            AnalyzeProjectPackageJob(
                job_id="b" * 32,
                request_id="r2",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
            )
        )
        store.mark_running("b" * 32)
        flagged = store.request_cancel("b" * 32)
        assert flagged is not None
        self.assertTrue(flagged.cancel_requested)
        self.assertEqual(flagged.status, JobStatus.RUNNING)
        cancelled = store.heartbeat("b" * 32)
        assert cancelled is not None
        self.assertEqual(cancelled.status, JobStatus.CANCELLED)

    def test_reclaim_stale_running_lease(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore(lease_seconds=60)
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        store.create(
            AnalyzeProjectPackageJob(
                job_id="c" * 32,
                request_id="r3",
                status=JobStatus.QUEUED,
                created_at=past,
            )
        )
        store.mark_running("c" * 32)
        # Force expired lease.
        running = store.get("c" * 32)
        assert running is not None
        from dataclasses import replace

        with store._lock:
            store._jobs["c" * 32] = replace(
                running,
                lease_expires_at=(datetime.now(tz=UTC) - timedelta(seconds=1)).isoformat(),
            )
        reclaimed = store.reclaim_stale_running()
        self.assertEqual(len(reclaimed), 1)
        self.assertEqual(reclaimed[0].status, JobStatus.FAILED)
        self.assertIn("Lease expired", reclaimed[0].error_message or "")

    def test_dead_letter_after_max_retries(self) -> None:
        store = InMemoryAnalyzeProjectPackageJobStore(max_retries=1)
        store.create(
            AnalyzeProjectPackageJob(
                job_id="d" * 32,
                request_id="r4",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
            )
        )
        store.mark_running("d" * 32)
        failed = store.mark_failed("d" * 32, "boom-1")
        assert failed is not None
        self.assertEqual(failed.status, JobStatus.FAILED)
        # Re-queue is not automatic; simulate restart claim path by creating new run
        # from FAILED is not allowed without re-queue. Direct second fail from RUNNING:
        store2 = InMemoryAnalyzeProjectPackageJobStore(max_retries=1)
        store2.create(
            AnalyzeProjectPackageJob(
                job_id="e" * 32,
                request_id="r5",
                status=JobStatus.QUEUED,
                created_at=datetime.now(tz=UTC).isoformat(),
                retry_count=1,
            )
        )
        store2.mark_running("e" * 32)
        dead = store2.mark_failed("e" * 32, "boom-2")
        assert dead is not None
        self.assertEqual(dead.status, JobStatus.DEAD_LETTER)


if __name__ == "__main__":
    unittest.main()
