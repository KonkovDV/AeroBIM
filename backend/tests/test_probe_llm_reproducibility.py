"""Unit tests for llm reproducibility probe compare logic."""

from __future__ import annotations

import unittest

from aerobim.tools.probe_llm_reproducibility import compare_runs


class ProbeLlmReproducibilityTests(unittest.TestCase):
    def test_matching_hashes_are_reproducible(self) -> None:
        run = {"status": "advisory", "draft_sha256": "abc"}
        report = compare_runs(run, dict(run), mode="intrasession")
        self.assertTrue(report["reproducible"])
        self.assertTrue(report["deterministic_intrasession"])
        self.assertIsNone(report["stable_across_time"])
        self.assertEqual(report["status"], "reproducible")

    def test_across_time_sets_p2_only(self) -> None:
        run = {"status": "advisory", "draft_sha256": "abc"}
        report = compare_runs(run, dict(run), mode="across_time")
        self.assertTrue(report["stable_across_time"])
        self.assertIsNone(report["deterministic_intrasession"])

    def test_mismatch_is_partial(self) -> None:
        report = compare_runs(
            {"status": "advisory", "draft_sha256": "a"},
            {"status": "advisory", "draft_sha256": "b"},
        )
        self.assertFalse(report["reproducible"])
        self.assertEqual(report["status"], "partial")


if __name__ == "__main__":
    unittest.main()
