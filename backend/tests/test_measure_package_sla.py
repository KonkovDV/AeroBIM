"""Tests for Samolet SLA measurement tool."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(result["schema_version"], "1.3.0")
        self.assertEqual(result["corpus_kind"], "fixture")
        self.assertEqual(result["claim_level"], "fixture_only")
        self.assertFalse(result["mandatory_capabilities_complete"])
        self.assertTrue(result["package_sha256"])
        self.assertEqual(result["pack_hash"], result["package_sha256"])
        self.assertEqual(result["machine_fingerprint"], result["machine"])
        self.assertIsInstance(result["file_inventory"], list)
        self.assertGreaterEqual(len(result["file_inventory"]), 1)
        self.assertIn("os", result["machine"])
        self.assertIn("cold_run", result)
        self.assertIn("warm_run", result)
        self.assertIn("command", result)
        self.assertIn("Fixture wall-clock only", result["allowed_wording"])

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

    def test_rejects_customer_measurable_without_mandatory_capabilities(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        with self.assertRaisesRegex(ValueError, "mandatory_capabilities_complete"):
            measure_package_sla(
                pack,
                max_minutes=30.0,
                corpus_kind="customer",
                claim_level="customer_measurable",
                mandatory_capabilities_complete=False,
            )

    def test_rejects_customer_measurable_without_machine_fingerprint(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        with patch(
            "aerobim.tools.measure_package_sla._machine_fingerprint",
            return_value={"os": "", "cpu": "", "ram_gb": None, "python": ""},
        ):
            with self.assertRaisesRegex(ValueError, "machine_fingerprint"):
                measure_package_sla(
                    pack,
                    max_minutes=30.0,
                    corpus_kind="customer",
                    claim_level="customer_measurable",
                    mandatory_capabilities_complete=True,
                )

    def test_customer_measurable_requires_full_evidence_gate(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        pack = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        result = measure_package_sla(
            pack,
            max_minutes=30.0,
            corpus_kind="customer",
            claim_level="customer_measurable",
            mandatory_capabilities_complete=True,
        )
        self.assertEqual(result["claim_level"], "customer_measurable")
        self.assertTrue(result["mandatory_capabilities_complete"])
        self.assertTrue(result["pack_hash"])
        self.assertTrue(result["machine_fingerprint"]["os"])
        self.assertEqual(result["allowed_wording"], "Customer package SLA measurement")


if __name__ == "__main__":
    unittest.main()
