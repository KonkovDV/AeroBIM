"""Optional Redis-backed analyze-job store for horizontal scale (W2.3).

Updates use Redis WATCH/MULTI compare-and-set and enforce job state transitions.
Bootstrap selects this store when ``AEROBIM_REDIS_URL`` is set.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime

from aerobim.domain.job_transitions import can_transition
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class RedisAnalyzeProjectPackageJobStore:
    def __init__(self, redis_url: str, *, key_prefix: str = "aerobim:jobs:") -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Redis job store requires the 'redis' package; install the 'enterprise' extra"
            ) from exc

        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._redis_mod = redis
        self._prefix = key_prefix

    def _key(self, job_id: str) -> str:
        return f"{self._prefix}{job_id}"

    def _serialize(self, job: AnalyzeProjectPackageJob) -> str:
        payload = asdict(job)
        payload["status"] = job.status.value
        return json.dumps(payload, ensure_ascii=False)

    def _deserialize(self, raw: str) -> AnalyzeProjectPackageJob:
        item = json.loads(raw)
        return AnalyzeProjectPackageJob(
            job_id=str(item["job_id"]),
            request_id=str(item["request_id"]),
            status=JobStatus(str(item["status"])),
            created_at=str(item["created_at"]),
            started_at=(str(item["started_at"]) if item.get("started_at") else None),
            completed_at=(str(item["completed_at"]) if item.get("completed_at") else None),
            report_id=str(item["report_id"]) if item.get("report_id") else None,
            error_message=(
                str(item["error_message"]) if item.get("error_message") is not None else None
            ),
        )

    def create(self, job: AnalyzeProjectPackageJob) -> str:
        created = self._redis.set(self._key(job.job_id), self._serialize(job), nx=True)
        if not created:
            raise ValueError(f"Job already exists: {job.job_id}")
        return job.job_id

    def get(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        raw = self._redis.get(self._key(job_id))
        if raw is None:
            return None
        return self._deserialize(raw)

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

    def _update(self, job_id: str, **changes: object) -> AnalyzeProjectPackageJob | None:
        key = self._key(job_id)
        target_status = changes.get("status")
        if not isinstance(target_status, JobStatus):
            raise TypeError("status must be a JobStatus")

        while True:
            try:
                with self._redis.pipeline() as pipe:
                    pipe.watch(key)
                    raw = pipe.get(key)
                    if raw is None:
                        pipe.unwatch()
                        return None
                    current = self._deserialize(raw)
                    if not can_transition(current.status, target_status):
                        pipe.unwatch()
                        return None
                    updated = replace(current, **changes)  # type: ignore[arg-type]
                    pipe.multi()
                    pipe.set(key, self._serialize(updated))
                    pipe.execute()
                    return updated
            except self._redis_mod.WatchError:
                continue
