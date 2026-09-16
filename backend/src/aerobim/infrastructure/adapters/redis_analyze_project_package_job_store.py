"""Optional Redis-backed analyze-job store for horizontal scale (W2.3).

Updates use Redis WATCH/MULTI compare-and-set and enforce job state transitions.
Bootstrap selects this store when ``AEROBIM_REDIS_URL`` is set.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import uuid4

from aerobim.domain.analyze_job_idempotency import (
    JobConcurrencyLimitError,
    job_from_stored_mapping,
)
from aerobim.domain.job_transitions import can_transition
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus

_DEFAULT_QUEUED_TTL_SECONDS = 600


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


class RedisAnalyzeProjectPackageJobStore:
    def __init__(
        self,
        redis_url: str,
        *,
        key_prefix: str = "aerobim:jobs:",
        queued_ttl_seconds: int = _DEFAULT_QUEUED_TTL_SECONDS,
    ) -> None:
        try:
            import redis
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Redis job store requires the 'redis' package; install the 'enterprise' extra"
            ) from exc

        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._redis_mod = redis
        self._prefix = key_prefix
        self._queued_ttl_seconds = queued_ttl_seconds
        self._lease_seconds = 120

    def _key(self, job_id: str) -> str:
        return f"{self._prefix}{job_id}"

    def _serialize(self, job: AnalyzeProjectPackageJob) -> str:
        payload = asdict(job)
        payload["status"] = job.status.value
        return json.dumps(payload, ensure_ascii=False)

    def _deserialize(self, raw: str) -> AnalyzeProjectPackageJob:
        item = json.loads(raw)
        return job_from_stored_mapping(item)

    def create(
        self,
        job: AnalyzeProjectPackageJob,
        *,
        max_concurrent_per_tenant: int | None = None,
    ) -> str:
        idem_index = (
            self._idempotency_key(job.idempotency_key, tenant_id=job.tenant_id)
            if job.idempotency_key
            else None
        )
        if job.idempotency_key:
            existing = self.get_by_idempotency_key(
                job.idempotency_key,
                tenant_id=job.tenant_id,
            )
            if existing is not None:
                return existing.job_id
        claimed_index = False
        if idem_index is not None:
            claimed_index = bool(self._redis.set(idem_index, job.job_id, nx=True))
            if not claimed_index:
                raced = self.get_by_idempotency_key(
                    job.idempotency_key or "",
                    tenant_id=job.tenant_id,
                )
                if raced is not None:
                    return raced.job_id
                dangling = self._redis.get(idem_index)
                if dangling and self.get(str(dangling)) is None:
                    self._redis.delete(idem_index)
                    claimed_index = bool(self._redis.set(idem_index, job.job_id, nx=True))
                if not claimed_index:
                    raise RuntimeError(
                        "Idempotency key claimed by concurrent submit; retry shortly"
                    )
        active_key = self._active_key(job.tenant_id) if job.tenant_id else None
        if max_concurrent_per_tenant is not None and max_concurrent_per_tenant > 0:
            tenant = (job.tenant_id or "").strip()
            if not tenant:
                if claimed_index and idem_index is not None:
                    self._redis.delete(idem_index)
                raise JobConcurrencyLimitError(
                    "Analyze job concurrency limit requires a bound tenant_id "
                    f"(limit {max_concurrent_per_tenant})"
                )
            active = int(self._redis.scard(active_key) or 0) if active_key else 0
            if active >= max_concurrent_per_tenant:
                if claimed_index and idem_index is not None:
                    self._redis.delete(idem_index)
                raise JobConcurrencyLimitError(
                    f"Tenant {tenant!r} has {active} active analyze jobs "
                    f"(limit {max_concurrent_per_tenant})"
                )
        try:
            created = self._redis.set(self._key(job.job_id), self._serialize(job), nx=True)
        except Exception:
            if claimed_index and idem_index is not None:
                self._redis.delete(idem_index)
            raise
        if not created:
            if claimed_index and idem_index is not None:
                self._redis.delete(idem_index)
            raise ValueError(f"Job already exists: {job.job_id}")
        if active_key is not None:
            self._redis.sadd(active_key, job.job_id)
        return job.job_id

    def get(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        raw = self._redis.get(self._key(job_id))
        if raw is None:
            return None
        return self._deserialize(str(raw))

    def get_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        tenant_id: str | None = None,
    ) -> AnalyzeProjectPackageJob | None:
        job_id = self._redis.get(self._idempotency_key(idempotency_key, tenant_id=tenant_id))
        if job_id is None:
            # Fallback scan for legacy keys written before the tenant-scoped index.
            wanted_tenant = (tenant_id or "").strip().casefold()
            for key in self._redis.scan_iter(match=f"{self._prefix}*"):
                key_str = str(key)
                if ":idem:" in key_str or ":active:" in key_str:
                    continue
                raw = self._redis.get(key)
                if raw is None:
                    continue
                job = self._deserialize(str(raw))
                if job.idempotency_key != idempotency_key:
                    continue
                if (job.tenant_id or "").strip().casefold() != wanted_tenant:
                    continue
                self._redis.set(
                    self._idempotency_key(idempotency_key, tenant_id=tenant_id),
                    job.job_id,
                )
                return job
            return None
        return self.get(str(job_id))

    def count_active_for_tenant(self, tenant_id: str) -> int:
        wanted = (tenant_id or "").strip().casefold()
        if not wanted:
            return 0
        count = 0
        for key in self._redis.scan_iter(match=f"{self._prefix}*"):
            key_str = str(key)
            if ":idem:" in key_str or ":active:" in key_str:
                continue
            raw = self._redis.get(key)
            if raw is None:
                continue
            job = self._deserialize(str(raw))
            if job.status not in {JobStatus.QUEUED, JobStatus.RUNNING}:
                continue
            if (job.tenant_id or "").strip().casefold() == wanted:
                count += 1
        return count

    def _active_key(self, tenant_id: str | None) -> str:
        tenant = (tenant_id or "").strip().casefold() or "_"
        return f"{self._prefix}active:{tenant}"

    def _idempotency_key(self, idempotency_key: str, *, tenant_id: str | None = None) -> str:
        tenant = (tenant_id or "").strip().casefold() or "_"
        return f"{self._prefix}idem:{tenant}:{idempotency_key}"

    def mark_running(
        self, job_id: str, *, owner: str | None = None
    ) -> AnalyzeProjectPackageJob | None:
        owner_token = (owner or uuid4().hex).strip() or uuid4().hex
        return self._update(
            job_id,
            status=JobStatus.RUNNING,
            started_at=_now_iso(),
            require_status=JobStatus.QUEUED,
            lease_owner=owner_token,
        )

    def mark_succeeded(
        self, job_id: str, report_id: str, *, owner: str | None = None
    ) -> AnalyzeProjectPackageJob | None:
        return self._update(
            job_id,
            status=JobStatus.SUCCEEDED,
            report_id=report_id,
            completed_at=_now_iso(),
            error_message=None,
            require_owner=owner,
            lease_owner=None,
        )

    def mark_failed(
        self, job_id: str, error_message: str, *, owner: str | None = None
    ) -> AnalyzeProjectPackageJob | None:
        current = self.get(job_id)
        if current is None:
            return None
        if owner and current.lease_owner and current.lease_owner != owner:
            return None
        retries = current.retry_count + 1
        if retries > 3 and can_transition(current.status, JobStatus.DEAD_LETTER):
            return self._update(
                job_id,
                status=JobStatus.DEAD_LETTER,
                completed_at=_now_iso(),
                error_message=error_message,
                retry_count=retries,
                lease_expires_at=None,
                stage_progress="dead_letter",
                require_owner=owner,
                lease_owner=None,
            )
        return self._update(
            job_id,
            status=JobStatus.FAILED,
            completed_at=_now_iso(),
            error_message=error_message,
            retry_count=retries,
            lease_expires_at=None,
            stage_progress="failed",
            require_owner=owner,
            lease_owner=None,
        )

    def heartbeat(
        self, job_id: str, *, lease_seconds: int = 120, owner: str | None = None
    ) -> AnalyzeProjectPackageJob | None:
        from datetime import timedelta

        current = self.get(job_id)
        if current is None or current.status is not JobStatus.RUNNING:
            return None
        if current.cancel_requested:
            return self.mark_cancelled(job_id, "Cancelled by request")
        lease_until = (datetime.now(tz=UTC) + timedelta(seconds=lease_seconds)).isoformat()
        return self._update(
            job_id,
            status=JobStatus.RUNNING,
            heartbeat_at=_now_iso(),
            lease_expires_at=lease_until,
            require_status=JobStatus.RUNNING,
            require_owner=owner,
        )

    def request_cancel(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        current = self.get(job_id)
        if current is None:
            return None
        if current.status is JobStatus.QUEUED:
            return self.mark_cancelled(job_id, "Cancelled before start")
        if current.status is JobStatus.RUNNING:
            return self._update(
                job_id,
                status=JobStatus.RUNNING,
                cancel_requested=True,
                stage_progress="cancel_requested",
            )
        return current

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
        from datetime import timedelta

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

        now = _parse_iso(now_iso) or datetime.now(tz=UTC)
        reclaimed: list[AnalyzeProjectPackageJob] = []
        for key in self._redis.scan_iter(match=f"{self._prefix}*"):
            key_str = str(key)
            if ":idem:" in key_str or ":active:" in key_str:
                continue
            raw = self._redis.get(key)
            if raw is None:
                continue
            job = self._deserialize(str(raw))
            if job.status is not JobStatus.RUNNING:
                continue
            expires = _parse_iso(job.lease_expires_at) or _parse_iso(job.heartbeat_at)
            if expires is None:
                started = _parse_iso(job.started_at) or _parse_iso(job.created_at)
                if started is None:
                    continue
                expires = started + timedelta(seconds=120)
            if expires >= now:
                continue
            updated = self.mark_failed(
                job.job_id,
                "Lease expired; job marked failed for recovery/resubmit",
            )
            if updated is not None:
                reclaimed.append(updated)
        return reclaimed

    def reclaim_stale_queued(
        self, ttl_seconds: int | None = None, *, now_iso: str | None = None
    ) -> list[AnalyzeProjectPackageJob]:
        from datetime import timedelta

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

        ttl = (
            int(ttl_seconds)
            if ttl_seconds is not None
            else int(getattr(self, "_queued_ttl_seconds", _DEFAULT_QUEUED_TTL_SECONDS))
        )
        now = _parse_iso(now_iso) or datetime.now(tz=UTC)
        horizon = timedelta(seconds=max(ttl, 0))
        reclaimed: list[AnalyzeProjectPackageJob] = []
        for key in self._redis.scan_iter(match=f"{self._prefix}*"):
            key_str = str(key)
            if ":idem:" in key_str or ":active:" in key_str:
                continue
            raw = self._redis.get(key)
            if raw is None:
                continue
            job = self._deserialize(str(raw))
            if job.status is not JobStatus.QUEUED or job.started_at:
                continue
            created = _parse_iso(job.created_at)
            if created is None or created + horizon >= now:
                continue
            updated = self.mark_failed(job.job_id, "orphaned_before_start")
            if updated is not None:
                reclaimed.append(updated)
        return reclaimed

    def _update(self, job_id: str, **changes: object) -> AnalyzeProjectPackageJob | None:
        key = self._key(job_id)
        target_status = changes.get("status")
        if not isinstance(target_status, JobStatus):
            raise TypeError("status must be a JobStatus")
        require_status = changes.pop("require_status", None)
        require_owner = changes.pop("require_owner", None)

        while True:
            try:
                with self._redis.pipeline() as pipe:
                    pipe.watch(key)
                    raw = pipe.get(key)
                    if raw is None:
                        pipe.unwatch()
                        return None
                    current = self._deserialize(str(raw))
                    if require_status is not None and current.status is not require_status:
                        pipe.unwatch()
                        return None
                    if (
                        require_owner
                        and current.lease_owner
                        and current.lease_owner != require_owner
                    ):
                        pipe.unwatch()
                        return None
                    if current.status is not target_status and not can_transition(
                        current.status, target_status
                    ):
                        pipe.unwatch()
                        return None
                    updated = replace(current, **changes)  # type: ignore[arg-type]
                    pipe.multi()
                    pipe.set(key, self._serialize(updated))
                    active_key = self._active_key(updated.tenant_id or current.tenant_id)
                    if updated.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                        pipe.sadd(active_key, job_id)
                    else:
                        pipe.srem(active_key, job_id)
                    pipe.execute()
                    return updated
            except self._redis_mod.WatchError:
                continue
