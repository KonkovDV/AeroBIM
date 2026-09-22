"""Optional Redis-backed analyze-job store for horizontal scale (W2.3).

Updates use Redis WATCH/MULTI compare-and-set and enforce job state transitions.
Bootstrap selects this store when ``AEROBIM_REDIS_URL`` is set.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aerobim.domain.analyze_job_idempotency import (
    JobConcurrencyLimitError,
    job_from_stored_mapping,
)
from aerobim.domain.job_transitions import abandoned_without_report, can_transition
from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus

_DEFAULT_QUEUED_TTL_SECONDS = 600

_CREATE_LUA = """
local job_key = KEYS[1]
local idem_key = KEYS[2]
local active_key = KEYS[3]
local job_id = ARGV[1]
local payload = ARGV[2]
local limit = tonumber(ARGV[3]) or 0
if idem_key ~= '' then
  local existing = redis.call('GET', idem_key)
  if existing then
    local prefix = string.sub(job_key, 1, string.len(job_key) - string.len(job_id))
    if redis.call('EXISTS', prefix .. existing) == 1 then
      return existing
    end
    return redis.error_reply('idempotency_pending')
  end
end
if active_key ~= '' and limit > 0 then
  if redis.call('SCARD', active_key) >= limit then
    return redis.error_reply('concurrency')
  end
end
if idem_key ~= '' then
  if redis.call('SET', idem_key, job_id, 'NX') == false then
    return redis.error_reply('idempotency_pending')
  end
end
if redis.call('SET', job_key, payload, 'NX') == false then
  if idem_key ~= '' then
    redis.call('DEL', idem_key)
  end
  return redis.error_reply('exists')
end
if active_key ~= '' then
  redis.call('SADD', active_key, job_id)
end
return job_id
"""


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


def _lease_expiry(job: AnalyzeProjectPackageJob, *, lease_seconds: int) -> datetime | None:
    expires = _parse_iso(job.lease_expires_at) or _parse_iso(job.heartbeat_at)
    if expires is not None:
        return expires
    started = _parse_iso(job.started_at) or _parse_iso(job.created_at)
    if started is None:
        return None
    return started + timedelta(seconds=lease_seconds)


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
        self._max_retries = 3

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
        tenant = (job.tenant_id or "").strip()
        limit = int(max_concurrent_per_tenant or 0)
        if limit > 0 and not tenant:
            raise JobConcurrencyLimitError(
                f"Analyze job concurrency limit requires a bound tenant_id (limit {limit})"
            )
        active_key = self._active_key(job.tenant_id) if job.tenant_id else ""
        try:
            result = self._redis.eval(
                _CREATE_LUA,
                3,
                self._key(job.job_id),
                idem_index or "",
                active_key,
                job.job_id,
                self._serialize(job),
                limit,
            )
        except self._redis_mod.ResponseError as exc:
            msg = str(exc)
            if "concurrency" in msg:
                raise JobConcurrencyLimitError(
                    f"Tenant {tenant!r} has active analyze jobs (limit {limit})"
                ) from exc
            if "idempotency_pending" in msg:
                raced = self.get_by_idempotency_key(
                    job.idempotency_key or "",
                    tenant_id=job.tenant_id,
                )
                if raced is not None:
                    return raced.job_id
                raise RuntimeError(
                    "Idempotency key claimed by concurrent submit; retry shortly"
                ) from exc
            if "exists" in msg:
                raise ValueError(f"Job already exists: {job.job_id}") from exc
            raise
        return str(result)

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
        lease_until = (datetime.now(tz=UTC) + timedelta(seconds=self._lease_seconds)).isoformat()
        return self._update(
            job_id,
            status=JobStatus.RUNNING,
            started_at=_now_iso(),
            heartbeat_at=_now_iso(),
            lease_expires_at=lease_until,
            stage_progress="running",
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
            expires = _lease_expiry(job, lease_seconds=self._lease_seconds)
            if expires is None or expires >= now:
                continue
            retries = job.retry_count + 1
            exhausted = retries > int(getattr(self, "_max_retries", 3))
            updated = self._update(
                job.job_id,
                status=JobStatus.DEAD_LETTER if exhausted else JobStatus.FAILED,
                completed_at=_now_iso(),
                error_message=(
                    "Lease expired; retry budget exhausted"
                    if exhausted
                    else "Lease expired; job marked failed for recovery/resubmit"
                ),
                retry_count=retries,
                lease_expires_at=None,
                stage_progress="dead_letter" if exhausted else "lease_expired",
                lease_owner=None,
                require_status=JobStatus.RUNNING,
                require_lease_expired_before=now,
            )
            if updated is not None:
                reclaimed.append(updated)
        return reclaimed

    def requeue_failed_without_report(self, job_id: str) -> AnalyzeProjectPackageJob | None:
        current = self.get(job_id)
        if not abandoned_without_report(current, max_retries=3):
            return None
        return self._update(
            job_id,
            status=JobStatus.QUEUED,
            started_at=None,
            completed_at=None,
            error_message=None,
            heartbeat_at=None,
            lease_expires_at=None,
            lease_owner=None,
            stage_progress="requeued",
            require_status=JobStatus.FAILED,
        )

    def requeue_abandoned_failures(self) -> list[AnalyzeProjectPackageJob]:
        requeued: list[AnalyzeProjectPackageJob] = []
        for key in self._redis.scan_iter(match=f"{self._prefix}*"):
            key_str = str(key)
            if ":idem:" in key_str or ":active:" in key_str:
                continue
            raw = self._redis.get(key)
            if raw is None:
                continue
            job = self._deserialize(str(raw))
            updated = self.requeue_failed_without_report(job.job_id)
            if updated is not None:
                requeued.append(updated)
        return requeued

    def reclaim_stale_queued(
        self, ttl_seconds: int | None = None, *, now_iso: str | None = None
    ) -> list[AnalyzeProjectPackageJob]:
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
        require_lease_expired_before = changes.pop("require_lease_expired_before", None)

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
                    if require_lease_expired_before is not None:
                        cutoff = require_lease_expired_before
                        if not isinstance(cutoff, datetime):
                            cutoff = _parse_iso(str(cutoff))
                        expires = _lease_expiry(current, lease_seconds=self._lease_seconds)
                        if cutoff is None or expires is None or expires >= cutoff:
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
