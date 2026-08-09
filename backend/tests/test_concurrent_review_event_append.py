"""N-33 / A-2: review-event sequence must stay unique under concurrent append."""

from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from aerobim.domain.review_event_append import ReviewEventAppendSpec
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    FilesystemReviewEventStore,
    HitlStateConflictError,
)


class ConcurrentReviewEventAppendTests(unittest.TestCase):
    def test_exactly_one_accept_wins_under_parallel_writers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp), fail_closed=True)
            report_id = "a" * 32
            store.append_api_event(
                ReviewEventAppendSpec(
                    report_id=report_id,
                    event_type="opened",
                    created_at="2026-08-09T12:00:00+00:00",
                    issue_rule_id="R1",
                    actor="seed",
                    note="seed",
                    latency_ms=1,
                    finding_id="f1",
                    previous_state=None,
                    idempotency_key="seed",
                    event_id=None,
                )
            )

            workers = 8
            barrier = threading.Barrier(workers)
            accepted_sequences: list[int] = []
            conflicts = 0
            lock = threading.Lock()

            def worker(idx: int) -> None:
                nonlocal conflicts
                barrier.wait()
                try:
                    event = store.append_api_event(
                        ReviewEventAppendSpec(
                            report_id=report_id,
                            event_type="accepted",
                            created_at="2026-08-09T12:00:01+00:00",
                            issue_rule_id="R1",
                            actor=f"actor-{idx}",
                            note="accept",
                            latency_ms=1,
                            finding_id="f1",
                            previous_state="opened",
                            idempotency_key=f"idem-{idx}",
                            event_id=None,
                        )
                    )
                    with lock:
                        accepted_sequences.append(event.sequence_number)
                except HitlStateConflictError:
                    with lock:
                        conflicts += 1

            threads = [threading.Thread(target=worker, args=(i,)) for i in range(workers)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            events = store.list_for_report(report_id)
            sequences = [event.sequence_number for event in events]
            self.assertEqual(accepted_sequences, [2])
            self.assertEqual(conflicts, workers - 1)
            self.assertEqual(sequences, [1, 2])
            self.assertEqual(len(sequences), len(set(sequences)))


if __name__ == "__main__":
    unittest.main()
