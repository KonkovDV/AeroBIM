"""Region quality gate: bad/unknown quality never becomes 'no violations' (P1).

READABLE requires positive evidence (known-good dpi + no negative trigger); worst
severity wins; only READABLE is usable_for_auto_read. Verdict-neutral.
"""

from __future__ import annotations

import json
import math
import unittest

from aerobim.domain.region_quality import (
    RegionQuality,
    RegionQualitySignals,
    assess_region_quality,
)


def _q(**kwargs: object) -> RegionQuality:
    return assess_region_quality(RegionQualitySignals(**kwargs)).quality  # type: ignore[arg-type]


class RegionQualityTests(unittest.TestCase):
    def test_no_signals_is_review_required(self) -> None:
        self.assertEqual(_q(), RegionQuality.REVIEW_REQUIRED)

    def test_very_low_dpi_is_unreadable(self) -> None:
        self.assertEqual(_q(dpi=50, has_text=True), RegionQuality.UNREADABLE)

    def test_moderate_low_dpi_is_low_quality(self) -> None:
        self.assertEqual(_q(dpi=120, has_text=True), RegionQuality.LOW_QUALITY)

    def test_high_skew_is_unreadable(self) -> None:
        self.assertEqual(_q(dpi=300, skew_deg=20), RegionQuality.UNREADABLE)

    def test_moderate_skew_is_low_quality(self) -> None:
        self.assertEqual(_q(dpi=300, skew_deg=8), RegionQuality.LOW_QUALITY)

    def test_no_text_is_unreadable(self) -> None:
        self.assertEqual(_q(dpi=300, has_text=False), RegionQuality.UNREADABLE)

    def test_low_text_count_is_low_quality(self) -> None:
        self.assertEqual(_q(dpi=300, has_text=True, text_char_count=1), RegionQuality.LOW_QUALITY)

    def test_good_signals_is_readable_and_usable(self) -> None:
        result = assess_region_quality(
            RegionQualitySignals(dpi=300, skew_deg=1, has_text=True, text_char_count=40)
        )
        self.assertEqual(result.quality, RegionQuality.READABLE)
        self.assertTrue(result.usable_for_auto_read())

    def test_unknown_resolution_cannot_confirm_readable(self) -> None:
        # HONESTY: no negative trigger but dpi unknown -> REVIEW_REQUIRED, never READABLE.
        result = assess_region_quality(RegionQualitySignals(skew_deg=1, has_text=True))
        self.assertEqual(result.quality, RegionQuality.REVIEW_REQUIRED)
        self.assertFalse(result.usable_for_auto_read())

    def test_worst_severity_wins(self) -> None:
        # dpi LOW + skew UNREADABLE -> UNREADABLE.
        self.assertEqual(_q(dpi=120, skew_deg=20, has_text=True), RegionQuality.UNREADABLE)

    def test_only_readable_is_usable_for_auto_read(self) -> None:
        for signals in (
            RegionQualitySignals(),  # review_required
            RegionQualitySignals(dpi=50, has_text=True),  # unreadable
            RegionQualitySignals(dpi=120, has_text=True),  # low_quality
        ):
            self.assertFalse(assess_region_quality(signals).usable_for_auto_read())

    def test_to_dict_json_safe_and_verdict_neutral(self) -> None:
        record = assess_region_quality(
            RegionQualitySignals(dpi=300, skew_deg=1, has_text=True, text_char_count=40)
        ).to_dict()
        json.dumps(record)
        self.assertNotIn('"passed"', json.dumps(record))
        self.assertEqual(record["quality"], "readable")
        self.assertTrue(record["usable_for_auto_read"])

    def test_nan_dpi_is_never_readable(self) -> None:
        # Red Team HIGH: NaN comparisons are all False; NaN dpi must NOT fall through to READABLE.
        result = assess_region_quality(RegionQualitySignals(dpi=float("nan"), has_text=True))
        self.assertEqual(result.quality, RegionQuality.REVIEW_REQUIRED)
        self.assertFalse(result.usable_for_auto_read())

    def test_inf_dpi_is_never_readable(self) -> None:
        result = assess_region_quality(RegionQualitySignals(dpi=math.inf, has_text=True))
        self.assertFalse(result.usable_for_auto_read())

    def test_nan_skew_normalizes_to_unknown(self) -> None:
        # NaN skew is treated as unknown (like None): with known-good dpi -> READABLE.
        self.assertEqual(_q(dpi=300, skew_deg=float("nan"), has_text=True), RegionQuality.READABLE)

    def test_boundary_dpi_floor_is_low_quality(self) -> None:
        self.assertEqual(_q(dpi=72, has_text=True), RegionQuality.LOW_QUALITY)


if __name__ == "__main__":
    unittest.main()
