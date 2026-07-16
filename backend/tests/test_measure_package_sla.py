"""Tests for Samolet SLA measurement tool."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.measure_package_sla import measure_package_sla


class MeasurePackageSlaTests(unittest.TestCase):
    def test_pilot_moscow_pack_meets_30_minute_sla(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        self.assertTrue(pack.exists(), f"Missing pack: {pack}")

        result = measure_package_sla(pack, max_minutes=30.0, iterations=1, warmup_iterations=0)

        self.assertTrue(result["sla_pass"])
        self.assertLessEqual(result["max_minutes_observed"], 30.0)
        self.assertEqual(result["artifact_type"], "samolet_package_sla")
        self.assertEqual(result["schema_version"], "1.2.0")
        self.assertEqual(result["corpus_kind"], "fixture")
        self.assertEqual(result["claim_level"], "fixture_only")
        self.assertTrue(result["package_sha256"])
        self.assertIsInstance(result["file_inventory"], list)
        self.assertGreaterEqual(len(result["file_inventory"]), 1)
        self.assertIn("os", result["machine"])
        self.assertIn("cold_run", result)
        self.assertIn("warm_run", result)
        self.assertIn("command", result)

    def test_rejects_customer_measurable_on_fixture_corpus(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        with self.assertRaises(ValueError):
            measure_package_sla(
                pack,
                max_minutes=30.0,
                corpus_kind="fixture",
                claim_level="customer_measurable",
            )


if __name__ == "__main__":
    unittest.main()
