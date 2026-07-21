"""Package trace collector tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from aerobim.domain.architecture import Contour, StageBudget
from aerobim.domain.package_trace import PackageTraceCollector


class PackageTraceCollectorTests(unittest.TestCase):
    def test_records_contour_elapsed(self) -> None:
        collector = PackageTraceCollector()
        with patch("aerobim.domain.package_trace.perf_counter", side_effect=[0.0, 1.5]):
            with collector.span(Contour.INGESTION):
                pass
        self.assertEqual(collector.elapsed(Contour.INGESTION), 1.5)
        self.assertEqual(collector.bottleneck_contour(), Contour.INGESTION.value)

    def test_recommendations_when_over_budget_ratio(self) -> None:
        budget = StageBudget(
            ingestion_minutes=0.01,
            deterministic_validation_minutes=20,
            ai_advisory_minutes=2,
            evidence_reporting_minutes=5,
        )
        collector = PackageTraceCollector(stage_budget=budget)
        collector.record(Contour.INGESTION, 1.0)
        hints = collector.recommendations()
        self.assertTrue(any("bottleneck_contour=ingestion" in item for item in hints))


if __name__ == "__main__":
    unittest.main()
