"""7-day freshness allowlist for live docs/evidence *latest.json."""

from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))
_fresh = importlib.import_module("check_live_evidence_freshness")


class LiveEvidenceFreshnessTests(unittest.TestCase):
    def test_allowlist_is_live_pins_not_frozen_benches(self) -> None:
        names = set(_fresh.LIVE_LATEST_JSON)
        self.assertIn("weekly-eng-status-latest.json", names)
        self.assertIn("tz-matrix-status-latest.json", names)
        self.assertIn("defect-injection-recall-run-latest.json", names)
        self.assertIn("sla-package-scale-latest.json", names)
        self.assertIn("data-residency-inventory-latest.json", names)
        self.assertIn("substitution-matrix-latest.json", names)
        self.assertNotIn("aecv-bench-eval-latest.json", names)
        self.assertNotIn("runtime-baseline-latest.json", names)

    def test_missing_and_stale_fail(self) -> None:
        now = datetime(2026, 9, 15, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fresh = {
                "generated_at": (now - timedelta(days=1)).isoformat(),
            }
            stale = {
                "generated_at": (now - timedelta(days=8)).isoformat(),
            }
            (root / "weekly-eng-status-latest.json").write_text(json.dumps(fresh), encoding="utf-8")
            (root / "tz-matrix-status-latest.json").write_text(json.dumps(stale), encoding="utf-8")
            errors = _fresh.collect_errors(root, now=now, max_age_days=7)
        blob = "\n".join(errors)
        self.assertIn("tz-matrix-status-latest.json", blob)
        self.assertIn("missing", blob)
        self.assertTrue(any("8d old" in err or "is 8d old" in err for err in errors))

    def test_fresh_allowlist_passes(self) -> None:
        now = datetime(2026, 9, 15, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = json.dumps({"generated_at": now.isoformat()})
            for name in _fresh.LIVE_LATEST_JSON:
                (root / name).write_text(payload, encoding="utf-8")
            self.assertEqual(_fresh.collect_errors(root, now=now, max_age_days=7), [])

    def test_committed_sla_scale_is_fixture_not_customer(self) -> None:
        payload = json.loads(
            (_REPO / "docs" / "evidence" / "sla-package-scale-latest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(payload["representative_scale"])
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertNotEqual(payload["claim_level"], "customer_measurable")
        self.assertFalse(payload["customer_go"])
        blob = json.dumps(payload)
        self.assertNotIn("C:/", blob)
        self.assertNotIn("C:\\", blob)
        honesty = payload["scale_honesty"]
        self.assertEqual(
            honesty["representative_scale_basis"],
            "referenced_file_inventory_not_analyze_rss",
        )
        self.assertGreater(
            int(honesty["unanalyzed_referenced_bytes"]),
            int(honesty["analyze_path_bytes"]),
        )


if __name__ == "__main__":
    unittest.main()
