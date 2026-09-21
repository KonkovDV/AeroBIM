"""Dedicated package-analysis worker; the API never executes queued IFC analysis."""

from __future__ import annotations

import os
import signal
import time

from aerobim.core.di.tokens import Tokens
from aerobim.domain.models import JobStatus
from aerobim.infrastructure.adapters.redis_analyze_job_queue import (
    RedisAnalyzeJobQueue,
)
from aerobim.infrastructure.di.bootstrap import bootstrap_container

_TERMINAL = {
    JobStatus.SUCCEEDED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
    JobStatus.DEAD_LETTER,
}


def main() -> None:
    container = bootstrap_container()
    settings = container.resolve(Tokens.SETTINGS)
    if not settings.redis_url:
        raise SystemExit("AEROBIM_REDIS_URL is required for the analyze worker")
    queue = RedisAnalyzeJobQueue(settings.redis_url)
    store = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_STORE)
    runner = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_JOB_RUNNER)
    logger = container.resolve(Tokens.LOGGER)
    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    recover_every = max(
        int(os.getenv("AEROBIM_WORKER_RECOVERY_SECONDS", "15")), 1
    )
    last_recovery = 0.0
    logger.info("dedicated analyze worker started")
    while not stopping:
        now = time.monotonic()
        if now - last_recovery >= recover_every:
            store.reclaim_stale_running()
            store.requeue_abandoned_failures()
            for job_id in queue.recover_processing():
                job = store.get(job_id)
                if job is None or job.status in _TERMINAL:
                    queue.ack(job_id)
                elif job.status is JobStatus.QUEUED:
                    queue.retry(job_id)
            last_recovery = now
        reserved = queue.reserve(timeout_seconds=2)
        if reserved is None:
            continue
        job_id, request = reserved
        runner.run(job_id, request)
        job = store.get(job_id)
        if job is None or job.status in _TERMINAL:
            queue.ack(job_id)
        # RUNNING/QUEUED remains unacked. Lease recovery will retry it after a
        # worker crash/OOM; fencing in the job store rejects duplicate commits.
    logger.info("dedicated analyze worker stopped")


if __name__ == "__main__":
    main()
