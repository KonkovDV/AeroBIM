"""
P0-C: Durable Job State Machine.

Formal state machine for heavy pipeline jobs.
Implements QUEUED→RUNNING→SUCCEEDED/FAILED/CANCEL_REQUESTED→CANCELLED/EXPIRED.
Heartbeat + stale recovery prevent lost jobs on worker restart.
Idempotency key (package_id+norm_pack_hash+engine_version) prevents
duplicate report/evidence on retry.

Reduces: reliability risk, auditability risk.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class StageStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCEL_REQUESTED, JobStatus.EXPIRED},
    JobStatus.RUNNING: {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCEL_REQUESTED, JobStatus.EXPIRED},
    JobStatus.CANCEL_REQUESTED: {JobStatus.CANCELLED, JobStatus.SUCCEEDED, JobStatus.FAILED},
    JobStatus.SUCCEEDED: set(),
    JobStatus.FAILED: {JobStatus.QUEUED},
    JobStatus.CANCELLED: set(),
    JobStatus.EXPIRED: {JobStatus.QUEUED},
}

HEARTBEAT_TIMEOUT_SECONDS = 120
MAX_RETRIES = 3


@dataclass
class StageProgress:
    stage_name: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    items_total: int = 0
    items_done: int = 0
    error_code: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        return {
            "stage_name": self.stage_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "items_total": self.items_total,
            "items_done": self.items_done,
            "error_code": self.error_code,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class JobRecord:
    """
    Persistent job record.

    idempotency_key: sha256(package_id+norm_pack_hash+engine_version+config_hash).
    Same inputs → same key → duplicate detection prevents double report.
    correlation_id: propagated through all log lines and traces.
    """
    job_id: str
    tenant_id: str
    project_id: str
    package_id: str
    idempotency_key: str
    correlation_id: str
    status: JobStatus = JobStatus.QUEUED
    retry_count: int = 0
    max_retries: int = MAX_RETRIES
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None
    stages: list[StageProgress] = field(default_factory=list)
    error_code: Optional[str] = None
    error_detail: Optional[str] = None
    result_report_id: Optional[str] = None
    cancel_reason: Optional[str] = None

    def transition(self, new_status: JobStatus) -> None:
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Illegal job transition {self.status} → {new_status} for job {self.job_id}"
            )
        self.status = new_status
        self.updated_at = datetime.now(tz=timezone.utc)
        if new_status == JobStatus.RUNNING:
            self.started_at = self.updated_at
        if new_status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.EXPIRED):
            self.finished_at = self.updated_at

    def heartbeat(self) -> None:
        self.last_heartbeat_at = datetime.now(tz=timezone.utc)
        self.updated_at = self.last_heartbeat_at

    def is_stale(self) -> bool:
        if self.status != JobStatus.RUNNING:
            return False
        if self.last_heartbeat_at is None:
            return True
        cutoff = datetime.now(tz=timezone.utc) - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
        return self.last_heartbeat_at < cutoff

    def can_retry(self) -> bool:
        return self.status in (JobStatus.FAILED, JobStatus.EXPIRED) and self.retry_count < self.max_retries

    def mark_failed(self, error_code: str, error_detail: str = "") -> None:
        self.error_code = error_code
        self.error_detail = error_detail
        self.transition(JobStatus.FAILED)

    def mark_succeeded(self, report_id: str) -> None:
        self.result_report_id = report_id
        self.transition(JobStatus.SUCCEEDED)

    def mark_cancelled(self, reason: str = "") -> None:
        self.cancel_reason = reason
        if self.status == JobStatus.CANCEL_REQUESTED:
            self.transition(JobStatus.CANCELLED)

    def expire_stale(self) -> None:
        self.transition(JobStatus.EXPIRED)

    def request_cancel(self) -> None:
        self.transition(JobStatus.CANCEL_REQUESTED)

    def get_stage(self, name: str) -> Optional[StageProgress]:
        for s in self.stages:
            if s.stage_name == name:
                return s
        return None

    def start_stage(self, name: str, items_total: int = 0) -> StageProgress:
        stage = self.get_stage(name)
        if stage is None:
            stage = StageProgress(stage_name=name)
            self.stages.append(stage)
        stage.status = StageStatus.RUNNING
        stage.started_at = datetime.now(tz=timezone.utc)
        stage.items_total = items_total
        return stage

    def finish_stage(self, name: str, success: bool = True) -> None:
        stage = self.get_stage(name)
        if stage:
            stage.status = StageStatus.SUCCEEDED if success else StageStatus.FAILED
            stage.finished_at = datetime.now(tz=timezone.utc)

    @property
    def progress_pct(self) -> int:
        if not self.stages:
            return 0 if self.status == JobStatus.QUEUED else 100
        done = sum(1 for s in self.stages if s.status in (StageStatus.SUCCEEDED, StageStatus.SKIPPED))
        return int(done * 100 / len(self.stages))

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "package_id": self.package_id,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "stages": [s.to_dict() for s in self.stages],
            "error_code": self.error_code,
            "error_detail": self.error_detail,
            "result_report_id": self.result_report_id,
            "cancel_reason": self.cancel_reason,
            "progress_pct": self.progress_pct,
        }


def make_idempotency_key(package_id: str, norm_pack_hash: str, engine_version: str, configuration_hash: str) -> str:
    payload = f"{package_id}|{norm_pack_hash}|{engine_version}|{configuration_hash}".encode()
    return hashlib.sha256(payload).hexdigest()[:40]


def new_job(tenant_id: str, project_id: str, package_id: str, idempotency_key: str) -> JobRecord:
    return JobRecord(
        job_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        project_id=project_id,
        package_id=package_id,
        idempotency_key=idempotency_key,
        correlation_id=str(uuid.uuid4()),
    )
