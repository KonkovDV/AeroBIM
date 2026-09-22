from __future__ import annotations

import threading
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.analyze_job_idempotency import (
    IdempotencyPayloadConflictError,
    JobConcurrencyLimitError,
    analyze_job_payload_fingerprint,
    fingerprints_conflict,
)
from aerobim.domain.job_state import (
    JobRecord,
    JobStatus as DomainJobStatus,
    new_job,
)
from aerobim.domain.logging import StructuredLogger
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus, ValidationRequest
from aerobim.domain.ports import AnalyzeProjectPackageJobStore, AuditReportStore

# Stage names used for JobRecord stage-progress tracking.
_STAGE_INGESTION = "ingestion"
_STAGE_DETERMINISTIC = "deterministic_validation"
_STAGE_EVIDENCE = "evidence_assembly"

_JOB_STATUS_TO_DOMAIN: dict[JobStatus, DomainJobStatus] = {
    JobStatus.QUEUED: DomainJobStatus.QUEUED,
    JobStatus.RUNNING: DomainJobStatus.RUNNING,
    JobStatus.SUCCEEDED: DomainJobStatus.SUCCEEDED,
    JobStatus.FAILED: DomainJobStatus.FAILED,
    JobStatus.CANCELLED: DomainJobStatus.CANCELLED,
}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _make_job_record(job_id: str, tenant_id: str | None, package_id: str) -> JobRecord:
    """Build a transient JobRecord for in-runner stage tracking.

    The record is local to the runner invocation; it is NOT persisted to the
    job store.  Its sole purpose is to enforce the domain state machine and
    emit granular progress into structured logs.
    """
    return new_job(
        tenant_id=tenant_id or "__anon__",
        project_id="__runner__",
        package_id=package_id or job_id,
        idempotency_key=job_id,
    )


class _LeaseHeartbeat:
    """Extend the job lease on a side thread while analyze runs."""

    def __init__(
        self,
        job_store: AnalyzeProjectPackageJobStore,
        job_id: str,
        *,
        owner: str,
        interval_seconds: float,
        lease_seconds: int,
    ) -> None:
        self._job_store = job_store
        self._job_id = job_id
        self._owner = owner
        self._interval = max(float(interval_seconds), 0.05)
        self._lease_seconds = lease_seconds
        self._stop = threading.Event()
        self._lost = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run,
            name=f"job-lease-{self._job_id[:8]}",
            daemon=True,
        )
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                beat = self._job_store.heartbeat(
                    self._job_id,
                    lease_seconds=self._lease_seconds,
                    owner=self._owner,
                )
            except Exception:
                self._lost.set()
                return
            if beat is None or beat.status is not JobStatus.RUNNING:
                self._lost.set()
                return

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=2.0)

    def lost(self) -> bool:
        return self._lost.is_set()


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
        idempotency_key = (idempotency_key or "").strip() or None
        fingerprint = analyze_job_payload_fingerprint(request)
        # Opportunistic reclaim before concurrency accounting / create.
        # QUEUED rows whose delivery never reached a worker fail closed after the TTL.
        self._job_store.reclaim_stale_running()
        self._job_store.reclaim_stale_queued()
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
                if fingerprints_conflict(existing.payload_fingerprint, fingerprint):
                    raise IdempotencyPayloadConflictError(
                        "Idempotency-Key already used with a different payload"
                    )
                return existing
        if max_concurrent_per_tenant is not None and max_concurrent_per_tenant > 0:
            # RT D09: deny anonymous/null tenant when a concurrency limit is configured.
            if tenant_id is None:
                raise JobConcurrencyLimitError(
                    "Analyze job concurrency limit requires a bound tenant_id "
                    f"(limit {max_concurrent_per_tenant})"
                )
        job = AnalyzeProjectPackageJob(
            job_id=uuid4().hex,
            request_id=request.request_id,
            status=JobStatus.QUEUED,
            created_at=_now_iso(),
            idempotency_key=idempotency_key,
            tenant_id=tenant_id,
            payload_fingerprint=fingerprint,
        )
        created_id = self._job_store.create(
            job, max_concurrent_per_tenant=max_concurrent_per_tenant
        )
        if created_id != job.job_id:
            recovered = self._job_store.get(created_id)
            if recovered is not None:
                if fingerprints_conflict(recovered.payload_fingerprint, fingerprint):
                    raise IdempotencyPayloadConflictError(
                        "Idempotency-Key already used with a different payload"
                    )
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
        audit_report_store: AuditReportStore | None = None,
    ) -> None:
        self._analyze_use_case = analyze_use_case
        self._job_store = job_store
        self._logger = logger
        self._audit_report_store = audit_report_store

    def _discard_report(self, report_id: str) -> None:
        store = self._audit_report_store
        if store is None:
            store = getattr(self._analyze_use_case, "_audit_report_store", None)
        discard = getattr(store, "discard", None)
        if callable(discard):
            discard(report_id)

    def _report_store(self) -> AuditReportStore | None:
        if self._audit_report_store is not None:
            return self._audit_report_store
        candidate = getattr(self._analyze_use_case, "_audit_report_store", None)
        return candidate if candidate is not None else None

    # ------------------------------------------------------------------
    # Stage helpers — forward to JobRecord and emit progress into logs
    # ------------------------------------------------------------------

    def _begin_stage(
        self,
        record: JobRecord,
        stage_name: str,
        *,
        job_id: str,
        request_id: str,
    ) -> None:
        record.start_stage(stage_name)
        self._logger.info(
            "analyze_project_package async job stage started",
            job_id=job_id,
            request_id=request_id,
            stage=stage_name,
            progress_pct=record.progress_pct,
        )

    def _end_stage(
        self,
        record: JobRecord,
        stage_name: str,
        *,
        job_id: str,
        request_id: str,
        success: bool = True,
    ) -> None:
        record.finish_stage(stage_name, success=success)
        self._logger.info(
            "analyze_project_package async job stage finished",
            job_id=job_id,
            request_id=request_id,
            stage=stage_name,
            success=success,
            progress_pct=record.progress_pct,
            stages=[s.to_dict() for s in record.stages],
        )

    def run(self, job_id: str, request: ValidationRequest) -> None:
        owner = uuid4().hex
        claimed = self._job_store.mark_running(job_id, owner=owner)
        if claimed is None:
            # Missing job, illegal transition, or second claim against RUNNING.
            self._logger.info(
                "analyze_project_package async job skip (not claimable)",
                job_id=job_id,
                request_id=request.request_id,
            )
            return

        # Build a local JobRecord and drive the domain state machine.
        # The record is NOT persisted; it enforces transitions and tracks stages.
        record = _make_job_record(
            job_id,
            getattr(claimed, "tenant_id", None),
            getattr(claimed, "package_id", None) or job_id,
        )
        try:
            record.transition(DomainJobStatus.RUNNING)
        except ValueError:
            # Defensive: record starts QUEUED, RUNNING is always allowed.
            pass

        if claimed.cancel_requested:
            self._job_store.mark_cancelled(job_id, "Cancelled before execution")
            return
        report_store = self._report_store()
        get_report = getattr(report_store, "get", None)
        existing_report = get_report(job_id) if callable(get_report) else None
        if existing_report is not None:
            if existing_report.request_id != request.request_id:
                self._job_store.mark_failed(job_id, "durable_report_identity_conflict", owner=owner)
                self._logger.error(
                    "analyze_project_package durable report identity conflict",
                    job_id=job_id,
                    request_id=request.request_id,
                )
                return
            self._job_store.mark_succeeded(job_id, existing_report.report_id, owner=owner)
            self._logger.info(
                "analyze_project_package async job adopted committed report",
                job_id=job_id,
                request_id=request.request_id,
                report_id=existing_report.report_id,
            )
            return
        self._logger.info(
            "analyze_project_package async job started",
            job_id=job_id,
            request_id=request.request_id,
        )
        lease_seconds = int(getattr(self._job_store, "_lease_seconds", 120) or 120)
        keeper = _LeaseHeartbeat(
            self._job_store,
            job_id,
            owner=owner,
            interval_seconds=max(lease_seconds / 3.0, 0.05),
            lease_seconds=lease_seconds,
        )
        keeper.start()
        report = None
        try:
            beat = self._job_store.heartbeat(job_id, lease_seconds=lease_seconds, owner=owner)
            if beat is not None and beat.status is JobStatus.CANCELLED:
                self._logger.info(
                    "analyze_project_package async job cancelled",
                    job_id=job_id,
                    request_id=request.request_id,
                )
                return
            if beat is None or keeper.lost():
                self._logger.error(
                    "analyze_project_package async job lost lease before analyze",
                    job_id=job_id,
                    request_id=request.request_id,
                )
                return
            try:
                execution_request = replace(request, report_id_override=job_id)
            except TypeError:
                execution_request = request

            # --- Stage: ingestion -------------------------------------------
            self._begin_stage(record, _STAGE_INGESTION, job_id=job_id, request_id=request.request_id)
            # Ingestion is the first phase executed inside analyze_use_case.execute().
            # We mark it finished optimistically after execute() returns;
            # if execute() raises, the except block marks it failed below.

            # --- Stage: deterministic_validation (wired inside execute) ------
            self._begin_stage(record, _STAGE_DETERMINISTIC, job_id=job_id, request_id=request.request_id)

            report = self._analyze_use_case.execute(execution_request)

            self._end_stage(record, _STAGE_DETERMINISTIC, job_id=job_id, request_id=request.request_id)
            self._end_stage(record, _STAGE_INGESTION, job_id=job_id, request_id=request.request_id)

            # --- Stage: evidence_assembly ------------------------------------
            self._begin_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id)

            if keeper.lost():
                self._end_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id, success=False)
                self._discard_report(report.report_id)
                self._logger.error(
                    "analyze_project_package async job lost lease during analyze",
                    job_id=job_id,
                    request_id=request.request_id,
                    report_id=report.report_id,
                )
                return
            beat = self._job_store.heartbeat(job_id, lease_seconds=lease_seconds, owner=owner)
            if beat is None:
                self._end_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id, success=False)
                self._discard_report(report.report_id)
                self._logger.error(
                    "analyze_project_package async job lost lease after analyze",
                    job_id=job_id,
                    request_id=request.request_id,
                    report_id=report.report_id,
                )
                return
            if beat.status is JobStatus.CANCELLED:
                self._end_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id, success=False)
                self._discard_report(report.report_id)
                self._logger.info(
                    "analyze_project_package async job cancelled after analyze",
                    job_id=job_id,
                    request_id=request.request_id,
                    report_id=report.report_id,
                )
                return
            if beat.cancel_requested:
                self._end_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id, success=False)
                self._discard_report(report.report_id)
                self._job_store.mark_cancelled(job_id, "Cancelled after analyze")
                return

            self._end_stage(record, _STAGE_EVIDENCE, job_id=job_id, request_id=request.request_id)

        except Exception as exc:
            # Mark any open stages as failed.
            for stage in record.stages:
                from aerobim.domain.job_state import StageStatus
                if stage.status is StageStatus.RUNNING:
                    record.finish_stage(stage.stage_name, success=False)
            try:
                record.transition(DomainJobStatus.FAILED)
            except ValueError:
                pass
            self._job_store.mark_failed(job_id, str(exc), owner=owner)
            self._logger.error(
                "analyze_project_package async job failed",
                job_id=job_id,
                request_id=request.request_id,
                detail=str(exc),
                stages=[s.to_dict() for s in record.stages],
            )
            return
        finally:
            keeper.stop()

        if report is None or keeper.lost():
            return

        try:
            record.transition(DomainJobStatus.SUCCEEDED)
        except ValueError:
            pass

        succeeded = self._job_store.mark_succeeded(job_id, report.report_id, owner=owner)
        if succeeded is None:
            self._discard_report(report.report_id)
            self._logger.error(
                "analyze_project_package async job commit rejected (lease/owner)",
                job_id=job_id,
                request_id=request.request_id,
                report_id=report.report_id,
            )
            return
        self._logger.info(
            "analyze_project_package async job completed",
            job_id=job_id,
            request_id=request.request_id,
            report_id=report.report_id,
            progress_pct=record.progress_pct,
            stages=[s.to_dict() for s in record.stages],
        )
