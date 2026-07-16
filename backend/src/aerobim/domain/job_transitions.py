"""Allowed transitions for analyze-project-package async jobs."""

from __future__ import annotations

from aerobim.domain.models import JobStatus

_ALLOWED_TRANSITIONS: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.QUEUED: frozenset({JobStatus.RUNNING, JobStatus.FAILED}),
    JobStatus.RUNNING: frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED}),
    JobStatus.SUCCEEDED: frozenset(),
    JobStatus.FAILED: frozenset(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())
