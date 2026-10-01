"""Allowed transitions for analyze-project-package async jobs."""

from __future__ import annotations

from aerobim.domain.models import JobStatus

_ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED}),
    JobStatus.RUNNING: frozenset(
        {
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
            JobStatus.DEAD_LETTER,
        }
    ),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset({JobStatus.QUEUED}),  # explicit retry re-queue
    JobStatus.CANCELLED: frozenset(),
    JobStatus.DEAD_LETTER: frozenset(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())


def abandoned_without_report(job: object, *, max_retries: int) -> bool:
    """True when a failed job may be queued again because it never published a report.

    Business failures stay failed. Only lease expiry and process-restart interrupts qualify.
    """

    status = getattr(job, "status", None)
    if job is None or status is not JobStatus.FAILED or getattr(job, "report_id", None):
        return False
    if int(getattr(job, "retry_count", 0) or 0) > max_retries:
        return False
    if not can_transition(status, JobStatus.QUEUED):
        return False
    message = str(getattr(job, "error_message", "") or "")
    return getattr(job, "stage_progress", None) == "lease_expired" or message.startswith(
        "Interrupted by process restart"
    )
