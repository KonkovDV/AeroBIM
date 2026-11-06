from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.drawing_region_hitl import (
    issues_for_hitl_regions,
    mark_regions_for_hitl,
    review_events_for_hitl_regions,
)
from aerobim.domain.models import DrawingRegionRef
from aerobim.infrastructure.adapters.filesystem_review_event_store import (
    FilesystemReviewEventStore,
)


class DrawingRegionHitlTests(unittest.TestCase):
    def test_low_confidence_detector_requires_hitl(self) -> None:
        regions = (
            DrawingRegionRef(
                sheet_id="AR-01",
                bbox_xyxy=(0.0, 0.0, 1.0, 0.85),
                confidence=0.35,
                modality="detector",
            ),
        )
        marked = mark_regions_for_hitl(regions, ())
        self.assertTrue(marked[0].hitl_required)
        self.assertIn("low_confidence", marked[0].hitl_reason or "")
        issues = issues_for_hitl_regions(marked)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule_id, "AEROBIM-DRAWING-REGION-HITL")
        self.assertEqual(issues[0].severity.value, "info")
        self.assertIsNotNone(issues[0].problem_zone)
        self.assertEqual(issues[0].problem_zone.sheet_id, "AR-01")

    def test_layout_priors_on_one_sheet_are_one_note(self) -> None:
        regions = tuple(
            DrawingRegionRef(
                sheet_id="ЭК",
                bbox_xyxy=(0.0, 0.0, 1.0, 0.5),
                confidence=0.3,
                modality="detector",
                coordinate_system="normalized-0-1",
                layout_role=role,
                hitl_required=True,
                hitl_reason="low_confidence<0.45",
            )
            for role in ("content", "stamp", "title_block", "specification", "dimension_chain")
        )
        issues = issues_for_hitl_regions(regions)
        self.assertEqual(len(issues), 1)
        self.assertIn("5 bands", issues[0].message)
        self.assertEqual(issues[0].problem_zone.sheet_id, "ЭК")

    def test_ocr_regions_not_escalated(self) -> None:
        regions = (
            DrawingRegionRef(
                sheet_id="AR-01",
                bbox_xyxy=(0.1, 0.1, 0.2, 0.2),
                confidence=0.2,
                modality="ocr",
            ),
        )
        marked = mark_regions_for_hitl(regions, ())
        self.assertFalse(marked[0].hitl_required)

    def test_review_events_persist(self) -> None:
        regions = mark_regions_for_hitl(
            (
                DrawingRegionRef(
                    sheet_id="AR-01",
                    bbox_xyxy=(0.0, 0.85, 0.25, 1.0),
                    confidence=0.3,
                    modality="detector",
                ),
            ),
            (),
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = FilesystemReviewEventStore(Path(tmp))
            events = review_events_for_hitl_regions(
                report_id="rpt-hitl",
                regions=regions,
                created_at="2026-07-17T00:00:00Z",
            )
            for event in events:
                store.append(event)
            loaded = store.list_for_report("rpt-hitl")
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].event_type, "drawing_region_escalated")


if __name__ == "__main__":
    unittest.main()
