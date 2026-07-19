"""Phase 9: Redis job lease reclaim parity with in-memory store."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from aerobim.domain.models import AnalyzeProjectPackageJob, JobStatus
from aerobim.infrastructure.adapters.redis_analyze_project_package_job_store import (
    RedisAnalyzeProjectPackageJobStore,
)


class Phase9RedisReclaimTests(unittest.TestCase):
    def test_reclaim_stale_running_marks_failed(self) -> None:
        store = RedisAnalyzeProjectPackageJobStore.__new__(RedisAnalyzeProjectPackageJobStore)
        store._prefix = "aerobim:jobs:"
        store._redis_mod = MagicMock()
        past = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
        stale = AnalyzeProjectPackageJob(
            job_id="a" * 32,
            request_id="r1",
            status=JobStatus.RUNNING,
            created_at=past,
            started_at=past,
            lease_expires_at=(datetime.now(tz=UTC) - timedelta(seconds=1)).isoformat(),
            tenant_id="t1",
        )
        redis = MagicMock()
        redis.scan_iter.return_value = [f"aerobim:jobs:{stale.job_id}"]
        redis.get.return_value = store._serialize(stale) if hasattr(store, "_serialize") else None

        # Bind serialize/deserialize via real methods after __new__.
        real = RedisAnalyzeProjectPackageJobStore
        store._serialize = real._serialize.__get__(store, RedisAnalyzeProjectPackageJobStore)
        store._deserialize = real._deserialize.__get__(store, RedisAnalyzeProjectPackageJobStore)
        store._key = real._key.__get__(store, RedisAnalyzeProjectPackageJobStore)
        store.mark_failed = MagicMock(
            return_value=AnalyzeProjectPackageJob(
                job_id=stale.job_id,
                request_id="r1",
                status=JobStatus.FAILED,
                created_at=past,
                error_message="Lease expired; job marked failed for recovery/resubmit",
                tenant_id="t1",
            )
        )
        redis.get.return_value = store._serialize(stale)
        store._redis = redis

        reclaimed = RedisAnalyzeProjectPackageJobStore.reclaim_stale_running(store)
        self.assertEqual(len(reclaimed), 1)
        store.mark_failed.assert_called_once()
        self.assertEqual(reclaimed[0].status, JobStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
