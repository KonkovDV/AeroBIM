"""Recover abandoned analyze jobs without publishing a second report.

This helper is transport-agnostic; production invokes equivalent recovery from the
dedicated worker. It does not prove a customer pack, external CDE import, or
production OIDC. It only requeues jobs abandoned before a report id was stored.
"""

from __future__ import annotations

from collections.abc import Mapping

from aerobim.application.use_cases.analyze_project_package_jobs import (
    AnalyzeProjectPackageJobRunner,
)
from aerobim.domain.models import JobStatus, ValidationRequest
from aerobim.domain.ports import AnalyzeProjectPackageJobStore


def recover_abandoned_jobs(
    store: AnalyzeProjectPackageJobStore,
    runner: AnalyzeProjectPackageJobRunner,
    requests: Mapping[str, ValidationRequest],
    *,
    now_iso: str | None = None,
) -> list[str]:
    """Requeue abandoned failures, then run each still-queued job at most once.

    A job that already succeeded is left untouched, so a later recovery pass
    cannot publish a second report for the same job id.
    """

    store.reclaim_stale_running(now_iso=now_iso)
    store.requeue_abandoned_failures()
    started: list[str] = []
    for job_id, request in requests.items():
        current = store.get(job_id)
        if current is None or current.status is not JobStatus.QUEUED:
            continue
        runner.run(job_id, request)
        started.append(job_id)
    return started
