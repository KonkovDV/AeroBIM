"""Drawing-region assessment: quality gate + classifier composition (P1).

Honest composition: a non-readable region is never classified/auto-read; AUTO_READ
needs readable + known type. Verdict-neutral.
"""

from __future__ import annotations

import json
import unittest

from aerobim.domain.drawing_region_assessment import (
    RegionAction,
    assess_drawing_region,
)
from aerobim.domain.region_classifier import RegionType
from aerobim.domain.region_quality import RegionQuality, RegionQualitySignals

_READABLE = RegionQualitySignals(dpi=300, skew_deg=1, has_text=True, text_char_count=40)


class DrawingRegionAssessmentTests(unittest.TestCase):
    def test_readable_and_typed_is_auto_read(self) -> None:
        result = assess_drawing_region(text="Узел А", quality_signals=_READABLE)
        self.assertEqual(result.action, RegionAction.AUTO_READ)
        self.assertIsNotNone(result.classification)
        assert result.classification is not None
        self.assertEqual(result.classification.region_type, RegionType.NODE)

    def test_bad_scan_with_valid_text_is_not_classified(self) -> None:
        # ANTI-BAD-SCAN: an unreadable region must NOT be classified even if text looks valid.
        result = assess_drawing_region(
            text="Узел А", quality_signals=RegionQualitySignals(dpi=50, has_text=True)
        )
        self.assertEqual(result.action, RegionAction.EXPERT_REVIEW)
        self.assertIsNone(result.classification)
        self.assertEqual(result.quality, RegionQuality.UNREADABLE)

    def test_low_quality_is_not_classified(self) -> None:
        result = assess_drawing_region(
            text="Узел А", quality_signals=RegionQualitySignals(dpi=120, has_text=True)
        )
        self.assertEqual(result.action, RegionAction.EXPERT_REVIEW)
        self.assertEqual(result.quality, RegionQuality.LOW_QUALITY)
        self.assertIsNone(result.classification)

    def test_readable_but_unknown_type_is_expert_review(self) -> None:
        result = assess_drawing_region(text="некий свободный текст", quality_signals=_READABLE)
        self.assertEqual(result.action, RegionAction.EXPERT_REVIEW)
        self.assertIsNotNone(result.classification)
        assert result.classification is not None
        self.assertEqual(result.classification.region_type, RegionType.UNKNOWN)

    def test_no_signals_is_expert_review(self) -> None:
        result = assess_drawing_region(text="Узел А")
        self.assertEqual(result.action, RegionAction.EXPERT_REVIEW)
        self.assertEqual(result.quality, RegionQuality.REVIEW_REQUIRED)
        self.assertIsNone(result.classification)

    def test_to_dict_json_safe_and_verdict_neutral(self) -> None:
        record = assess_drawing_region(text="Узел А", quality_signals=_READABLE).to_dict()
        json.dumps(record)
        self.assertNotIn('"passed"', json.dumps(record))
        self.assertEqual(record["action"], "auto_read")
        self.assertEqual(record["quality"], "readable")
        self.assertIsNotNone(record["classification"])

    def test_to_dict_serializes_none_classification(self) -> None:
        record = assess_drawing_region(
            text="Узел А", quality_signals=RegionQualitySignals(dpi=50, has_text=True)
        ).to_dict()
        json.dumps(record)
        self.assertIsNone(record["classification"])
        self.assertEqual(record["action"], "expert_review")


if __name__ == "__main__":
    unittest.main()
