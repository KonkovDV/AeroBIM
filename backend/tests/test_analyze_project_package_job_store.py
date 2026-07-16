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


if __name__ == "__main__":
    unittest.main()
