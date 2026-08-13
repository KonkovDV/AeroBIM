"""Sprint 3 open-corpus battery tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from aerobim.tools.run_open_corpora_profiles import (
    _load_known_upstream_case_ids,
    _regression_pass_stats,
    repo_root,
)

CASE_0101_ID = (
    "pass-specification_version_is_purely_metadata_and_does_not_impact_"
    "pass_or_fail_result"
)


class RegressionPassStatsTests(unittest.TestCase):
    def test_upstream_edge_excluded_from_fail(self) -> None:
        rows = [
            {"case_id": "pass-an_optional_attribute_passes_if_null", "match": False},
            {"case_id": "other-pass", "match": True},
        ]
        known = frozenset({"pass-an_optional_attribute_passes_if_null"})
        stats = _regression_pass_stats(rows, known_upstream=known)
        self.assertTrue(stats["regression_pass"])
        self.assertEqual(stats["known_upstream_mismatch_count"], 1)
        self.assertEqual(stats["unexplained_mismatch_count"], 0)

    def test_unexplained_mismatch_fails(self) -> None:
        rows = [{"case_id": "broken", "match": False}]
        stats = _regression_pass_stats(rows, known_upstream=frozenset())
        self.assertFalse(stats["regression_pass"])

    def test_fail_closed_divergence_is_labeled_not_unexplained(self) -> None:
        rows = [{"case_id": CASE_0101_ID, "match": False}]
        stats = _regression_pass_stats(
            rows,
            known_upstream=frozenset(),
            fail_closed=frozenset({CASE_0101_ID}),
        )
        self.assertTrue(stats["regression_pass"])
        self.assertEqual(stats["fail_closed_divergence_count"], 1)
        self.assertEqual(stats["unexplained_mismatch_count"], 0)

    def test_loads_fail_closed_0101(self) -> None:
        from aerobim.tools.run_open_corpora_profiles import _load_fail_closed_divergence_ids

        ids = _load_fail_closed_divergence_ids(repo_root())
        self.assertIn(CASE_0101_ID, ids)


class KnownUpstreamLoaderTests(unittest.TestCase):
    def test_loads_case_0017(self) -> None:
        known = _load_known_upstream_case_ids(repo_root())
        self.assertIn("pass-an_optional_attribute_passes_if_null", known)


class Sprint3BatterySmokeTests(unittest.TestCase):
    def test_battery_quick_passes(self) -> None:
        from aerobim.tools.run_sprint3_open_corpus_battery import run_battery

        with patch(
            "aerobim.tools.run_sprint3_open_corpus_battery._run_internal_script",
            return_value={"status": "skipped"},
        ):
            payload = run_battery(include_bsi=False, run_internal=False)
        self.assertTrue(payload["battery_pass"])
        regression = payload["open_corpora"]["profiles"]["regression"]
        self.assertEqual(regression["cases_matched"], regression["cases_run"])


if __name__ == "__main__":
    unittest.main()
