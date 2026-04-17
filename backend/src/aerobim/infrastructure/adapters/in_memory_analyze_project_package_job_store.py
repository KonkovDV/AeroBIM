from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from threading import Lock

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class InMemoryAnalyzeProjectPackageJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, AnalyzeProjectPackageJob] = {}
        self._lock = Lock()

    def create(self, job: AnalyzeProjectPackageJob) -> str:
        with self._lock:
            self._jobs[job.job_id] = job
        return job.job_id

    def get(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        return self._update(job_id, status=JobStatus.RUNNING, started_at=_now_iso())

    def mark_succeeded(self, job_id: str, report_id: str) -> AnalyzeProjectPackageJob | None:
        return self._update(
            job_id,
            status=JobStatus.SUCCEEDED,
            report_id=report_id,
            completed_at=_now_iso(),
            error_message=None,
        )

    def mark_failed(self, job_id: str, error_message: str) -> AnalyzeProjectPackageJob | None:
        return self._update(
            job_id,
            status=JobStatus.FAILED,
            completed_at=_now_iso(),
            error_message=error_message,
        )

    def _update(
        self,
        job_id: str,
        *,
        status: JobStatus,
        started_at: str | None = None,
        completed_at: str | None = None,
        report_id: str | None = None,
        error_message: str | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            updated = replace(
                job,
                status=status,
                started_at=started_at if started_at is not None else job.started_at,
                completed_at=completed_at if completed_at is not None else job.completed_at,
                report_id=report_id if report_id is not None else job.report_id,
                error_message=error_message,
            )
            self._jobs[job_id] = updated
            return updated
