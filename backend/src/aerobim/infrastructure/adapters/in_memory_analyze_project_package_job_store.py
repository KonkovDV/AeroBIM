from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock

from aerobim.domain.job_transitions import can_transition
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus

_DEFAULT_LEASE_SECONDS = 120
_MAX_RETRIES_BEFORE_DEAD_LETTER = 3


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class InMemoryAnalyzeProjectPackageJobStore:
    def __init__(
        self,
        snapshot_path: Path | None = None,
        *,
        lease_seconds: int = _DEFAULT_LEASE_SECONDS,
        max_retries: int = _MAX_RETRIES_BEFORE_DEAD_LETTER,
    ) -> None:
        self._jobs: dict[str, AnalyzeProjectPackageJob] = {}
        self._lock = Lock()
        self._snapshot_path = snapshot_path
        self._lease_seconds = lease_seconds
        self._max_retries = max_retries
        self._load_snapshot()

    def _load_snapshot(self) -> None:
        if self._snapshot_path is None or not self._snapshot_path.exists():
            return
        try:
            payload = json.loads(self._snapshot_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                f"Corrupt analyze-job snapshot at {self._snapshot_path}: {exc}"
            ) from exc

        if not isinstance(payload, list):
            raise RuntimeError(
                f"Corrupt analyze-job snapshot at {self._snapshot_path}: expected a JSON list"
            )

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
                    completed_at=(str(item["completed_at"]) if item.get("completed_at") else None),
                    report_id=str(item["report_id"]) if item.get("report_id") else None,
                    error_message=(
                        str(item["error_message"])
                        if item.get("error_message") is not None
                        else None
                    ),
                    idempotency_key=(
                        str(item["idempotency_key"]) if item.get("idempotency_key") else None
                    ),
                    heartbeat_at=(str(item["heartbeat_at"]) if item.get("heartbeat_at") else None),
                    lease_expires_at=(
                        str(item["lease_expires_at"]) if item.get("lease_expires_at") else None
                    ),
                    retry_count=int(item.get("retry_count") or 0),
                    stage_progress=(
                        str(item["stage_progress"]) if item.get("stage_progress") else None
                    ),
                    cancel_requested=bool(item.get("cancel_requested") or False),
                    tenant_id=(str(item["tenant_id"]) if item.get("tenant_id") else None),
                )
            except (KeyError, ValueError, TypeError):
                continue
            if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                job = replace(
                    job,
                    status=JobStatus.FAILED,
                    completed_at=_now_iso(),
                    error_message="Interrupted by process restart; resubmit the job",
                    lease_expires_at=None,
                )
            self._jobs[job.job_id] = job
        if self._jobs:
            self._persist_snapshot()

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
            if job.idempotency_key:
                existing = self._find_by_idempotency_key_unlocked(
                    job.idempotency_key,
                    tenant_id=job.tenant_id,
                )
                if existing is not None:
                    return existing.job_id
            self._jobs[job.job_id] = job
            self._persist_snapshot()
        return job.job_id

    def get(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        tenant_id: str | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            return self._find_by_idempotency_key_unlocked(
                idempotency_key,
                tenant_id=tenant_id,
            )

    def count_active_for_tenant(self, tenant_id: str) -> int:
        wanted = (tenant_id or "").strip().casefold()
        if not wanted:
            return 0
        with self._lock:
            self._reclaim_stale_unlocked(_now())
            return sum(
                1
                for job in self._jobs.values()
                if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}
                and (job.tenant_id or "").strip().casefold() == wanted
            )

    def _find_by_idempotency_key_unlocked(
        self,
        idempotency_key: str,
        *,
        tenant_id: str | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        wanted_tenant = (tenant_id or "").strip().casefold()
        for job in self._jobs.values():
            if job.idempotency_key != idempotency_key:
                continue
            job_tenant = (job.tenant_id or "").strip().casefold()
            if job_tenant == wanted_tenant:
                return job
        return None

    def mark_running(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        lease_until = (_now() + timedelta(seconds=self._lease_seconds)).isoformat()
        return self._update(
            job_id,
            status=JobStatus.RUNNING,
            started_at=_now_iso(),
            heartbeat_at=_now_iso(),
            lease_expires_at=lease_until,
            stage_progress="running",
        )

    def mark_succeeded(self, job_id: str, report_id: str) -> AnalyzeProjectPackageJob | None:
        return self._update(
            job_id,
            status=JobStatus.SUCCEEDED,
            report_id=report_id,
            completed_at=_now_iso(),
            error_message=None,
            lease_expires_at=None,
            stage_progress="succeeded",
        )

    def mark_failed(self, job_id: str, error_message: str) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            retries = job.retry_count + 1
            if retries > self._max_retries and can_transition(job.status, JobStatus.DEAD_LETTER):
                return self._update_unlocked(
                    job_id,
                    status=JobStatus.DEAD_LETTER,
                    completed_at=_now_iso(),
                    error_message=error_message,
                    retry_count=retries,
                    lease_expires_at=None,
                    stage_progress="dead_letter",
                )
            if not can_transition(job.status, JobStatus.FAILED):
                return None
            return self._update_unlocked(
                job_id,
                status=JobStatus.FAILED,
                completed_at=_now_iso(),
                error_message=error_message,
                retry_count=retries,
                lease_expires_at=None,
                stage_progress="failed",
            )

    def heartbeat(
        self, job_id: str, *, lease_seconds: int = 120
    ) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status is not JobStatus.RUNNING:
                return None
            if job.cancel_requested:
                return self._update_unlocked(
                    job_id,
                    status=JobStatus.CANCELLED,
                    completed_at=_now_iso(),
                    error_message="Cancelled by request",
                    lease_expires_at=None,
                    stage_progress="cancelled",
                )
            lease_until = (_now() + timedelta(seconds=lease_seconds)).isoformat()
            return self._update_unlocked(
                job_id,
                status=JobStatus.RUNNING,
                heartbeat_at=_now_iso(),
                lease_expires_at=lease_until,
            )

    def request_cancel(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.status is JobStatus.QUEUED and can_transition(job.status, JobStatus.CANCELLED):
                return self._update_unlocked(
                    job_id,
                    status=JobStatus.CANCELLED,
                    completed_at=_now_iso(),
                    error_message="Cancelled before start",
                    cancel_requested=True,
                    stage_progress="cancelled",
                )
            if job.status is JobStatus.RUNNING:
                updated = replace(job, cancel_requested=True, stage_progress="cancel_requested")
                self._jobs[job_id] = updated
                self._persist_snapshot()
                return updated
            return job

    def mark_cancelled(
        self, job_id: str, reason: str | None = None
    ) -> AnalyzeProjectPackageJob | None:
        return self._update(
            job_id,
            status=JobStatus.CANCELLED,
            completed_at=_now_iso(),
            error_message=reason or "Cancelled",
            lease_expires_at=None,
            cancel_requested=True,
            stage_progress="cancelled",
        )

    def reclaim_stale_running(
        self, *, now_iso: str | None = None
    ) -> list[AnalyzeProjectPackageJob]:
        with self._lock:
            now = _parse_iso(now_iso) or _now()
            return self._reclaim_stale_unlocked(now)

    def _reclaim_stale_unlocked(self, now: datetime) -> list[AnalyzeProjectPackageJob]:
        reclaimed: list[AnalyzeProjectPackageJob] = []
        for job_id, job in list(self._jobs.items()):
            if job.status is not JobStatus.RUNNING:
                continue
            expires = _parse_iso(job.lease_expires_at) or _parse_iso(job.heartbeat_at)
            # No lease metadata: treat as stale after default lease from started_at.
            if expires is None:
                started = _parse_iso(job.started_at) or _parse_iso(job.created_at)
                if started is None:
                    continue
                expires = started + timedelta(seconds=self._lease_seconds)
            if expires >= now:
                continue
            updated = self._update_unlocked(
                job_id,
                status=JobStatus.FAILED,
                completed_at=now.isoformat(),
                error_message="Lease expired; job marked failed for recovery/resubmit",
                retry_count=job.retry_count + 1,
                lease_expires_at=None,
                stage_progress="lease_expired",
            )
            if updated is not None:
                reclaimed.append(updated)
        return reclaimed

    def _update(
        self,
        job_id: str,
        *,
        status: JobStatus,
        started_at: str | None = None,
        completed_at: str | None = None,
        report_id: str | None = None,
        error_message: str | None = None,
        heartbeat_at: str | None = None,
        lease_expires_at: str | None | object = ...,
        retry_count: int | None = None,
        stage_progress: str | None = None,
        cancel_requested: bool | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        with self._lock:
            return self._update_unlocked(
                job_id,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                report_id=report_id,
                error_message=error_message,
                heartbeat_at=heartbeat_at,
                lease_expires_at=lease_expires_at,
                retry_count=retry_count,
                stage_progress=stage_progress,
                cancel_requested=cancel_requested,
            )

    def _update_unlocked(
        self,
        job_id: str,
        *,
        status: JobStatus,
        started_at: str | None = None,
        completed_at: str | None = None,
        report_id: str | None = None,
        error_message: str | None = None,
        heartbeat_at: str | None = None,
        lease_expires_at: str | None | object = ...,
        retry_count: int | None = None,
        stage_progress: str | None = None,
        cancel_requested: bool | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status is not status and not can_transition(job.status, status):
            return None
        updated = replace(
            job,
            status=status,
            started_at=started_at if started_at is not None else job.started_at,
            completed_at=completed_at if completed_at is not None else job.completed_at,
            report_id=report_id if report_id is not None else job.report_id,
            error_message=error_message if error_message is not None else job.error_message,
            heartbeat_at=heartbeat_at if heartbeat_at is not None else job.heartbeat_at,
            lease_expires_at=(
                job.lease_expires_at if lease_expires_at is ... else lease_expires_at  # type: ignore[arg-type]
            ),
            retry_count=retry_count if retry_count is not None else job.retry_count,
            stage_progress=stage_progress if stage_progress is not None else job.stage_progress,
            cancel_requested=(
                cancel_requested if cancel_requested is not None else job.cancel_requested
            ),
        )
        self._jobs[job_id] = updated
        self._persist_snapshot()
        return updated
