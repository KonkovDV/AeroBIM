from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class InMemoryAnalyzeProjectPackageJobStore:
    def __init__(self, snapshot_path: Path | None = None) -> None:
        self._jobs: dict[str, AnalyzeProjectPackageJob] = {}
        self._lock = Lock()
        self._snapshot_path = snapshot_path
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        if self._snapshot_path is None or not self._snapshot_path.exists():
            return
        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        if not isinstance(payload, list):
            return

        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                job = AnalyzeProjectPackageJob(
                    job_id=str(item["job_id"]),
                    request_id=str(item["request_id"]),
                    status=JobStatus(str(item["status"])),
                    created_at=str(item["created_at"]),
                    started_at=(str(item["started_at"]) if item.get("started_at") else None),
                    completed_at=(
                        str(item["completed_at"]) if item.get("completed_at") else None
                    ),
                    report_id=str(item["report_id"]) if item.get("report_id") else None,
                    error_message=(
                        str(item["error_message"])
                        if item.get("error_message") is not None
                        else None
                    ),
                )
            except (KeyError, ValueError):
                continue
            self._jobs[job.job_id] = job

    def _persist_snapshot(self) -> None:
        if self._snapshot_path is None:
            return
        self._snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        payload: list[dict[str, object]] = []
        for job in self._jobs.values():
            serialized = asdict(job)
            serialized["status"] = job.status.value
            payload.append(serialized)
        self._snapshot_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, job: AnalyzeProjectPackageJob) -> str:
        with self._lock:
            self._jobs[job.job_id] = job
            self._persist_snapshot()
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
            self._persist_snapshot()
            return updated
