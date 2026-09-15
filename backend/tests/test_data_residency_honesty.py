"""JOB-01 honesty and substitution-matrix token count."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.export_data_residency import build_payload as residency_payload
from aerobim.tools.export_substitution_matrix import token_names


class DataResidencyHonestyTests(unittest.TestCase):
    def test_job_01_does_not_claim_durable_workers(self) -> None:
        payload = residency_payload(generated_at="2026-09-15T00:00:00+00:00")
        job = payload["job_queue"]
        assert isinstance(job, dict)
        self.assertFalse(job["durable_workers_claimed"])
        self.assertIn("BackgroundTasks", str(job["honesty"]))
        self.assertFalse(payload["customer_go"])
        analyze = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "aerobim"
            / "presentation"
            / "http"
            / "routes"
            / "analyze.py"
        ).read_text(encoding="utf-8")
        self.assertIn("JOB-01", analyze)
        self.assertIn("not a durable", analyze.lower())


class SubstitutionTokenCountTests(unittest.TestCase):
    def test_token_names_match_tokens_class(self) -> None:
        names = token_names()
        self.assertGreaterEqual(len(names), 60)
        self.assertIn("IDS_VALIDATOR", names)
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
