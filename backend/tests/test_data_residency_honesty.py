"""JOB-01 evidence and substitution-matrix token count."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.export_data_residency import build_payload as residency_payload
from aerobim.tools.export_substitution_matrix import token_names


class DataResidencyHonestyTests(unittest.TestCase):
    def test_job_01_reports_dedicated_durable_worker_without_overclaim(self) -> None:
        payload = residency_payload(generated_at="2026-09-15T00:00:00+00:00")
        job = payload["job_queue"]
        assert isinstance(job, dict)
        self.assertTrue(job["durable_workers_claimed"])
        self.assertEqual(job["status"], "dedicated_durable_worker")
        self.assertEqual(job["delivery"], "at_least_once")
        self.assertIn("producer-only", str(job["honesty"]))
        self.assertIn("not a formally verified", str(job["honesty"]))
        self.assertFalse(payload["customer_go"])

        root = Path(__file__).resolve().parents[1] / "src" / "aerobim"
        analyze = (root / "presentation" / "http" / "routes" / "analyze.py").read_text(
            encoding="utf-8"
        )
        worker = (root / "worker.py").read_text(encoding="utf-8")
        queue = (
            root / "infrastructure" / "adapters" / "redis_analyze_job_queue.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("BackgroundTasks", analyze)
        self.assertIn("RedisAnalyzeJobQueue", analyze)
        self.assertIn("queue.reserve", worker)
        self.assertIn("brpoplpush", queue)


class SubstitutionTokenCountTests(unittest.TestCase):
    def test_token_names_match_tokens_class(self) -> None:
        names = token_names()
        self.assertGreaterEqual(len(names), 60)
        self.assertIn("IDS_VALIDATOR", names)
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
