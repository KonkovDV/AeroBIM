from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.logging import StructuredLogger
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus, ValidationRequest
from aerobim.domain.ports import AnalyzeProjectPackageJobStore


class JobConcurrencyLimitError(RuntimeError):
    """Raised when a tenant exceeds max concurrent QUEUED+RUNNING analyze jobs."""


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
        max_concurrent_per_tenant: int | None = None,
    ) -> AnalyzeProjectPackageJob:
        tenant_id = (request.tenant_id or "").strip() or None
        # Opportunistic reclaim before concurrency accounting / create.
        self._job_store.reclaim_stale_running()
        if idempotency_key:
            existing = self._job_store.get_by_idempotency_key(
                idempotency_key,
                tenant_id=tenant_id,
            )
            if existing is not None and existing.status in {
                JobStatus.QUEUED,
                JobStatus.RUNNING,
                JobStatus.SUCCEEDED,
            }:
                return existing
        if max_concurrent_per_tenant is not None and max_concurrent_per_tenant > 0:
            # RT D09: deny anonymous/null tenant when a concurrency limit is configured.
            if tenant_id is None:
                raise JobConcurrencyLimitError(
                    "Analyze job concurrency limit requires a bound tenant_id "
                    f"(limit {max_concurrent_per_tenant})"
                )
            active = self._job_store.count_active_for_tenant(tenant_id)
            if active >= max_concurrent_per_tenant:
                raise JobConcurrencyLimitError(
                    f"Tenant {tenant_id!r} has {active} active analyze jobs "
                    f"(limit {max_concurrent_per_tenant})"
                )
        job = AnalyzeProjectPackageJob(
            job_id=uuid4().hex,
            request_id=request.request_id,
            status=JobStatus.QUEUED,
            created_at=_now_iso(),
            idempotency_key=idempotency_key,
            tenant_id=tenant_id,
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
        # Do not globally reclaim on every status GET — that can FAIL a live runner.
        return self._job_store.get(job_id)


class CancelAnalyzeProjectPackageJobUseCase:
    def __init__(self, job_store: AnalyzeProjectPackageJobStore) -> None:
        self._job_store = job_store

    def execute(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        return self._job_store.request_cancel(job_id)


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
        if claimed.cancel_requested:
            self._job_store.mark_cancelled(job_id, "Cancelled before execution")
            return
        self._logger.info(
            "analyze_project_package async job started",
            job_id=job_id,
            request_id=request.request_id,
        )
        try:
            beat = self._job_store.heartbeat(job_id)
            if beat is not None and beat.status is JobStatus.CANCELLED:
                self._logger.info(
                    "analyze_project_package async job cancelled",
                    job_id=job_id,
                    request_id=request.request_id,
                )
                return
            report = self._analyze_use_case.execute(request)
            beat = self._job_store.heartbeat(job_id)
            if beat is not None and beat.status is JobStatus.CANCELLED:
                self._logger.info(
                    "analyze_project_package async job cancelled after analyze",
                    job_id=job_id,
                    request_id=request.request_id,
                )
                return
            if beat is not None and beat.cancel_requested:
                self._job_store.mark_cancelled(job_id, "Cancelled after analyze")
                return
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
