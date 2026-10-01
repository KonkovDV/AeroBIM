"""Stage-level timeout guard tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from aerobim.domain.architecture import Contour, StageBudget
from aerobim.domain.stage_timeout import (
    StageTimeoutExceeded,
    StageTimeoutGuard,
    contour_budget_seconds,
    enforce_stage_timeout,
)


class StageTimeoutTests(unittest.TestCase):
    def test_contour_budget_seconds_from_stage_budget(self) -> None:
        budget = StageBudget(
            ingestion_minutes=1,
            deterministic_validation_minutes=2,
            ai_advisory_minutes=3,
            evidence_reporting_minutes=4,
        )
        self.assertEqual(contour_budget_seconds(Contour.INGESTION, budget), 60.0)
        self.assertEqual(
            contour_budget_seconds(Contour.DETERMINISTIC_VALIDATION, budget),
            120.0,
        )

    def test_enforce_stage_timeout_raises_when_exceeded(self) -> None:
        budget = StageBudget(ingestion_minutes=0.01)
        with self.assertRaises(StageTimeoutExceeded) as ctx:
            enforce_stage_timeout(
                contour=Contour.INGESTION,
                elapsed_seconds=1.0,
                budget=budget,
            )
        self.assertEqual(ctx.exception.contour, Contour.INGESTION)

    def test_guard_passes_within_budget(self) -> None:
        budget = StageBudget(ingestion_minutes=10)
        with patch("aerobim.domain.stage_timeout.perf_counter", side_effect=[0.0, 0.5]):
            with StageTimeoutGuard(Contour.INGESTION, budget):
                pass

    def test_guard_raises_when_elapsed_exceeds_budget(self) -> None:
        budget = StageBudget(ingestion_minutes=0.01)
        with patch("aerobim.domain.stage_timeout.perf_counter", side_effect=[0.0, 2.0]):
            with self.assertRaises(StageTimeoutExceeded):
                with StageTimeoutGuard(Contour.INGESTION, budget):
                    pass


if __name__ == "__main__":
    unittest.main()
