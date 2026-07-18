"""Phase 5 HITL: actor rules, idempotent append, region page bounds."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.drawing_region_hitl import mark_regions_for_hitl
from aerobim.domain.models import DrawingRegionRef, ReviewEvent
from aerobim.domain.review_state_machine import HitlTransitionError, assert_hitl_transition
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    AuditEventCorruptionError,
    FilesystemReviewEventStore,
)


class Phase5HitlRulesTests(unittest.TestCase):
    def test_accepted_requires_actor(self) -> None:
        with self.assertRaises(HitlTransitionError):
            assert_hitl_transition(current="opened", event_type="accepted")

    def test_region_nan_confidence_and_page_bounds(self) -> None:
        regions = mark_regions_for_hitl(
            (
                DrawingRegionRef(
                    sheet_id="AR-01",
                    bbox_xyxy=(0.0, 0.0, 1.0, 1.0),
                    confidence=float("nan"),
                    modality="detector",
                ),
                DrawingRegionRef(
                    sheet_id="AR-01",
                    bbox_xyxy=(0.0, 0.0, 50.0, 50.0),
                    confidence=0.9,
                    modality="ocr",
                    page_width=10.0,
                    page_height=10.0,
                    coordinate_system="page-pixel",
                ),
            )
        )
        self.assertTrue(regions[0].hitl_required)
        self.assertIn("invalid_confidence", regions[0].hitl_reason or "")
        self.assertTrue(regions[1].hitl_required)
        self.assertEqual(regions[1].hitl_reason, "bbox_outside_page")
        self.assertTrue(math.isnan(float("nan")))

    def test_idempotent_append_and_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = FilesystemReviewEventStore(Path(temporary_directory), fail_closed=True)
            event = ReviewEvent(
                event_id="evt-1",
                report_id="r" * 32,
                event_type="opened",
                created_at="2026-07-18T00:00:00Z",
                actor="expert-1",
                note="triage start",
                idempotency_key="api:same-key",
                previous_state="escalated",
                resulting_state="opened",
            )
            first = store.append(event)
            second = store.append(event)
            self.assertEqual(first, second)
            listed = store.list_for_report("r" * 32)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0].sequence_number, 1)

    def test_corrupt_line_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            store = FilesystemReviewEventStore(root, fail_closed=True)
            report_id = "s" * 32
            path = root / "review-events" / f"{report_id}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{not-json\n", encoding="utf-8")
            with self.assertRaises(AuditEventCorruptionError):
                store.list_for_report(report_id)


if __name__ == "__main__":
    unittest.main()
