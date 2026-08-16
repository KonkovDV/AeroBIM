"""Task 7 — weekly eng status export (no invented funnel)."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.export_weekly_eng_status import build_weekly_status


class WeeklyEngStatusTests(unittest.TestCase):
    def test_build_includes_claim_boundary_and_owner_funnel(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        payload = build_weekly_status(repo=repo)
        self.assertEqual(payload["artifact_type"], "aerobim_weekly_eng_status")
        self.assertEqual(payload["checkpoint"], "NO_GO")
        self.assertEqual(payload["commercial_funnel"]["status"], "OWNER_ONLY")
        self.assertIn("No invented commercial funnel", payload["claim_boundary"])
        self.assertEqual(
            payload["pnst909_22_scenario_axis"]["cli"],
            "python -m aerobim.tools.run_pnst909_22_scenario_runtime",
        )
        self.assertTrue(
            str(payload["pnst909_22_scenario_axis"].get("runtime_generated_at") or "").startswith(
                "2026-08-05"
            )
        )
        self.assertEqual(
            payload["pnst909_22_scenario_axis"]["ishigaki_cli"],
            "python -m aerobim.tools.run_ishigaki_ids_bench_smoke",
        )
        self.assertAlmostEqual(payload["coverage_map"]["kr_detectable_share_approx"], 0.167)
        # R-4: commercial key must appear before eng blocks in insertion order.
        keys = list(payload.keys())
        self.assertLess(keys.index("commercial_funnel"), keys.index("runtime_baseline"))
        self.assertIn(
            payload["commercial_funnel"]["data_status"], {"MISSING", "PRESENT_OWNER_FILE"}
        )


if __name__ == "__main__":
    unittest.main()
