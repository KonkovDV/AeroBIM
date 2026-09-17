"""Phase 9: Redis job lease reclaim and Lua create (in-process fake Redis)."""

from __future__ import annotations

import fnmatch
import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import (
    _CREATE_LUA,
    RedisAnalyzeProjectPackageJobStore,
)


class _WatchError(Exception):
    pass


class _ResponseError(Exception):
    pass


class _FakePipe:
    def __init__(self, redis: _FakeRedis) -> None:
        self._r = redis
        self._watched: dict[str, str | None] = {}
        self._buffer: list[tuple[str, str, str]] = []
        self._multi = False

    def watch(self, key: str) -> None:
        self._watched[key] = self._r.kv.get(key)

    def get(self, key: str) -> str | None:
        return self._r.kv.get(key)

    def unwatch(self) -> None:
        self._watched.clear()

    def multi(self) -> None:
        self._multi = True
        self._buffer = []

    def set(self, key: str, value: str) -> None:
        if self._multi:
            self._buffer.append(("set", key, value))
        else:
            self._r.kv[key] = value

    def sadd(self, key: str, member: str) -> None:
        if self._multi:
            self._buffer.append(("sadd", key, member))
        else:
            self._r.sets.setdefault(key, set()).add(member)

    def srem(self, key: str, member: str) -> None:
        if self._multi:
            self._buffer.append(("srem", key, member))
        else:
            self._r.sets.setdefault(key, set()).discard(member)

    def execute(self) -> bool:
        hook = self._r.before_execute
        if hook is not None:
            hook()
        for key, expected in self._watched.items():
            if self._r.kv.get(key) != expected:
                raise _WatchError()
        for kind, key, value in self._buffer:
            if kind == "set":
                self._r.kv[key] = value
            elif kind == "sadd":
                self._r.sets.setdefault(key, set()).add(value)
            elif kind == "srem":
                self._r.sets.setdefault(key, set()).discard(value)
        self._multi = False
        self._buffer = []
        self._watched.clear()
        return True

    def __enter__(self) -> _FakePipe:
        return self

    def __exit__(self, *exc: object) -> bool:
        self._watched.clear()
        return False


class _FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}
        self.sets: dict[str, set[str]] = {}
        self.before_execute = None

    def pipeline(self) -> _FakePipe:
        return _FakePipe(self)

    def get(self, key: str) -> str | None:
        return self.kv.get(key)

    def scan_iter(self, match: str = "*"):
        for key in list(self.kv):
            if fnmatch.fnmatch(key, match):
                yield key

    def eval(self, script: str, numkeys: int, *args: object) -> str:
        if script != _CREATE_LUA:
            raise AssertionError("unexpected Lua script")
        job_key, idem_key, active_key = str(args[0]), str(args[1]), str(args[2])
        job_id, payload = str(args[3]), str(args[4])
        limit = int(args[5] or 0)
        if idem_key:
            existing = self.kv.get(idem_key)
            if existing is not None:
                prefix = job_key[: len(job_key) - len(job_id)]
                if prefix + existing in self.kv:
                    return existing
                raise _ResponseError("idempotency_pending")
        if active_key and limit > 0 and len(self.sets.get(active_key, set())) >= limit:
            raise _ResponseError("concurrency")
        if idem_key:
            if idem_key in self.kv:
                raise _ResponseError("idempotency_pending")
            self.kv[idem_key] = job_id
        if job_key in self.kv:
            if idem_key:
                self.kv.pop(idem_key, None)
            raise _ResponseError("exists")
        self.kv[job_key] = payload
        if active_key:
            self.sets.setdefault(active_key, set()).add(job_id)
        return job_id


def _store(fake: _FakeRedis) -> RedisAnalyzeProjectPackageJobStore:
    store = RedisAnalyzeProjectPackageJobStore.__new__(RedisAnalyzeProjectPackageJobStore)
    store._redis = fake
    store._redis_mod = SimpleNamespace(WatchError=_WatchError, ResponseError=_ResponseError)
    store._prefix = "aerobim:jobs:"
    store._lease_seconds = 120
    store._queued_ttl_seconds = 60
    return store


class Phase9RedisReclaimTests(unittest.TestCase):
    def test_reclaim_stale_running_marks_failed(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        stale = AnalyzeProjectPackageJob(
            job_id="a" * 32,
            request_id="r1",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            heartbeat_at=past,
            lease_expires_at=(datetime.now(tz=UTC) - timedelta(seconds=1)).isoformat(),
            tenant_id="t1",
        )
        fake.kv[store._key(stale.job_id)] = store._serialize(stale)
        reclaimed = store.reclaim_stale_running()
        self.assertEqual(len(reclaimed), 1)
        self.assertEqual(reclaimed[0].status, JobStatus.FAILED)
        self.assertEqual(store.get(stale.job_id).status, JobStatus.FAILED)  # type: ignore[union-attr]

    def test_reclaim_does_not_steal_refreshed_lease(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        future = (datetime.now(tz=UTC) + timedelta(minutes=2)).isoformat()
        stale = AnalyzeProjectPackageJob(
            job_id="c" * 32,
            request_id="r3",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            heartbeat_at=past,
            lease_expires_at=(datetime.now(tz=UTC) - timedelta(seconds=1)).isoformat(),
            lease_owner="worker-a",
            tenant_id="t1",
        )
        live = AnalyzeProjectPackageJob(
            job_id=stale.job_id,
            request_id="r3",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            heartbeat_at=future,
            lease_expires_at=future,
            lease_owner="worker-a",
            tenant_id="t1",
        )
        fake.kv[store._key(stale.job_id)] = store._serialize(stale)

        original_get = fake.get

        def _scan_then_heartbeat(key: str) -> str | None:
            raw = original_get(key)
            fake.kv[key] = store._serialize(live)
            return raw

        fake.get = _scan_then_heartbeat  # type: ignore[method-assign]
        reclaimed = store.reclaim_stale_running()
        self.assertEqual(reclaimed, [])
        self.assertEqual(store.get(stale.job_id).status, JobStatus.RUNNING)  # type: ignore[union-attr]
        self.assertEqual(store.get(stale.job_id).lease_owner, "worker-a")  # type: ignore[union-attr]

    def test_watch_error_retry_refuses_refreshed_lease(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        future = (datetime.now(tz=UTC) + timedelta(minutes=2)).isoformat()
        stale = AnalyzeProjectPackageJob(
            job_id="d" * 32,
            request_id="r4",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            heartbeat_at=past,
            lease_expires_at=(datetime.now(tz=UTC) - timedelta(seconds=1)).isoformat(),
            lease_owner="worker-a",
            tenant_id="t1",
        )
        live = AnalyzeProjectPackageJob(
            job_id=stale.job_id,
            request_id="r4",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            heartbeat_at=future,
            lease_expires_at=future,
            lease_owner="worker-a",
            tenant_id="t1",
        )
        key = store._key(stale.job_id)
        fake.kv[key] = store._serialize(stale)

        def _heartbeat_before_exec() -> None:
            fake.kv[key] = store._serialize(live)
            fake.before_execute = None

        fake.before_execute = _heartbeat_before_exec
        reclaimed = store.reclaim_stale_running()
        self.assertEqual(reclaimed, [])
        self.assertEqual(store.get(stale.job_id).lease_expires_at, future)  # type: ignore[union-attr]

    def test_reclaim_stale_queued_marks_failed(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        stale = AnalyzeProjectPackageJob(
            job_id="b" * 32,
            request_id="r2",
            status=JobStatus.QUEUED,
            created_at=past,
            tenant_id="t1",
        )
        fake.kv[store._key(stale.job_id)] = store._serialize(stale)
        reclaimed = store.reclaim_stale_queued()
        self.assertEqual(len(reclaimed), 1)
        self.assertEqual(reclaimed[0].status, JobStatus.FAILED)
        self.assertEqual(reclaimed[0].error_message, "orphaned_before_start")


class Phase9RedisCreateLuaTests(unittest.TestCase):
    def test_dangling_idempotency_reservation_is_not_stolen(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        job = AnalyzeProjectPackageJob(
            job_id="e" * 32,
            request_id="r5",
            status=JobStatus.QUEUED,
            created_at=datetime.now(tz=UTC).isoformat(),
            idempotency_key="idem-1",
            tenant_id="t1",
        )
        fake.kv[store._idempotency_key("idem-1", tenant_id="t1")] = "ghost-job"
        with self.assertRaisesRegex(RuntimeError, "Idempotency key claimed"):
            store.create(job)
        self.assertIsNone(store.get(job.job_id))
        self.assertEqual(fake.kv[store._idempotency_key("idem-1", tenant_id="t1")], "ghost-job")

    def test_create_persists_job_when_reservation_is_free(self) -> None:
        fake = _FakeRedis()
        store = _store(fake)
        job = AnalyzeProjectPackageJob(
            job_id="f" * 32,
            request_id="r6",
            status=JobStatus.QUEUED,
            created_at=datetime.now(tz=UTC).isoformat(),
            idempotency_key="idem-2",
            tenant_id="t1",
        )
        created = store.create(job)
        self.assertEqual(created, job.job_id)
        self.assertEqual(store.get(job.job_id).status, JobStatus.QUEUED)  # type: ignore[union-attr]
        again = store.create(job)
        self.assertEqual(again, job.job_id)


if __name__ == "__main__":
    unittest.main()
