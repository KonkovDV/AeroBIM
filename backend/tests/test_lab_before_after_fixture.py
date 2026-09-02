"""Lab before/after journal: tool elapsed only, manual timer stays empty."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.mik_commission_scoring import (
    foreign_labor_cut_as_ours,
    k4_revenue_claimed,
)
from aerobim.tools.run_lab_before_after_fixture import (
    DEFAULT_EVIDENCE_REL,
    DEFAULT_IDS_REL,
    DEFAULT_IFC_REL,
    build_journal,
    sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class LabBeforeAfterFixtureJournalTests(unittest.TestCase):
    def test_stub_journal_leaves_manual_empty_and_does_not_claim_k4(self) -> None:
        payload = build_journal(
            repo=REPO_ROOT,
            measured={"t_tool_ms": 42, "machine_issue_count": 0},
            generated_at="2026-09-02T00:00:00+00:00",
        )
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertFalse(payload["complete_for_formula"])
        self.assertFalse(payload["fills_a1_a8"])
        self.assertIsNone(payload["t_manual_s"])
        self.assertIsNone(payload["n_remarks_manual"])
        self.assertIsNone(payload["n_remarks_tool_confirmed"])
        self.assertIsNone(payload["order"])
        self.assertIsNone(payload["discrepancy"])
        self.assertEqual(payload["t_tool_ms"], 42)
        self.assertEqual(payload["t_tool_s"], 0)
        self.assertFalse(payload["k4_revenue_claimed"])
        self.assertFalse(payload["foreign_labor_cut_as_ours"])
        self.assertFalse(k4_revenue_claimed())
        self.assertFalse(foreign_labor_cut_as_ours())
        self.assertFalse(payload["closes_rt001"])
        ifc = REPO_ROOT / DEFAULT_IFC_REL
        ids = REPO_ROOT / DEFAULT_IDS_REL
        self.assertEqual(payload["pack_hash"], sha256_file(ifc))
        self.assertEqual(payload["ids_hash"], sha256_file(ids))

    def test_committed_evidence_journal_is_tool_only(self) -> None:
        path = REPO_ROOT / DEFAULT_EVIDENCE_REL
        self.assertTrue(path.is_file(), path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertIsNone(payload["t_manual_s"])
        self.assertFalse(payload["complete_for_formula"])
        self.assertFalse(payload["fills_a1_a8"])
        self.assertIsInstance(payload["t_tool_ms"], int)
        self.assertGreaterEqual(payload["t_tool_ms"], 0)
        self.assertEqual(
            payload["pack_hash"],
            sha256_file(REPO_ROOT / DEFAULT_IFC_REL),
        )

    def test_protocol_points_at_tool_only_journal(self) -> None:
        protocol = (
            REPO_ROOT / "docs" / "partners" / "BEFORE_AFTER_MEASUREMENT_PROTOCOL_2026_09.md"
        ).read_text(encoding="utf-8")
        self.assertIn("lab-before-after-fixture-tool-only-latest.json", protocol)
        self.assertIn("t_manual_s", protocol.lower())


class LabBeforeAfterCliTests(unittest.TestCase):
    def test_main_writes_json(self) -> None:
        from aerobim.tools.run_lab_before_after_fixture import main

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "journal.json"
            code = main(
                [
                    "--repo",
                    str(REPO_ROOT),
                    "--output",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertIsNone(payload["t_manual_s"])
        self.assertIsInstance(payload["t_tool_ms"], int)


if __name__ == "__main__":
    unittest.main()
