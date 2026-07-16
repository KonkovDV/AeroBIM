from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.logging import StructuredLogger
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus, ValidationRequest
from aerobim.domain.ports import AnalyzeProjectPackageJobStore


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class SubmitAnalyzeProjectPackageJobUseCase:
    def __init__(self, job_store: AnalyzeProjectPackageJobStore) -> None:
        self._job_store = job_store

    def execute(
        self,
        request: ValidationRequest,
        *,
        idempotency_key: str | None = None,
    ) -> AnalyzeProjectPackageJob:
        if idempotency_key:
            existing = self._job_store.get_by_idempotency_key(idempotency_key)
            if existing is not None and existing.status in {
                JobStatus.QUEUED,
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,
            }:
                return existing
        job = AnalyzeProjectPackageJob(
            job_id=uuid4().hex,
            request_id=request.request_id,
            status=JobStatus.QUEUED,
            created_at=_now_iso(),
            idempotency_key=idempotency_key,
        )
        created_id = self._job_store.create(job)
        if created_id != job.job_id:
            recovered = self._job_store.get(created_id)
            if recovered is not None:
                return recovered
        return job


class GetAnalyzeProjectPackageJobStatusUseCase:
    def __init__(self, job_store: AnalyzeProjectPackageJobStore) -> None:
        self._job_store = job_store

    def execute(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        return self._job_store.get(job_id)


class AnalyzeProjectPackageJobRunner:
    def __init__(
        self,
        analyze_use_case: AnalyzeProjectPackageUseCase,
        job_store: AnalyzeProjectPackageJobStore,
        logger: StructuredLogger,
    ) -> None:
        self._analyze_use_case = analyze_use_case
        self._job_store = job_store
        self._logger = logger

    def run(self, job_id: str, request: ValidationRequest) -> None:
        claimed = self._job_store.mark_running(job_id)
        if claimed is None:
            # Missing job, illegal transition, or idempotent retry against terminal state.
            self._logger.info(
                "analyze_project_package async job skip (not claimable)",
                job_id=job_id,
                request_id=request.request_id,
            )
            return
        self._logger.info(
            "analyze_project_package async job started",
            job_id=job_id,
            request_id=request.request_id,
        )
        try:
            report = self._analyze_use_case.execute(request)
        except Exception as exc:
            self._job_store.mark_failed(job_id, str(exc))
            self._logger.error(
                "analyze_project_package async job failed",
                job_id=job_id,
                request_id=request.request_id,
                detail=str(exc),
            )
            return

        self._job_store.mark_succeeded(job_id, report.report_id)
        self._logger.info(
            "analyze_project_package async job completed",
            job_id=job_id,
            request_id=request.request_id,
            report_id=report.report_id,
        )
