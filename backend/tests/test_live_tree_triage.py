"""Live-tree Red Team triage stays NO_GO and encodes KILL brakes."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.domain.live_tree_triage import TRIAGE_ROWS, triage_snapshot
from aerobim.domain.tz_v1_brief import (
    PAPER_OBJECTS,
    mik_act_may_cite_tz_v1_accuracy_as_measured,
    v1_brief_snapshot,
)


class LiveTreeTriageTests(unittest.TestCase):
    def test_snapshot_stays_no_go(self) -> None:
        snap = triage_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")
        self.assertEqual(snap["detected_count"], 0)
        self.assertFalse(snap["closes_rt001"])
        self.assertFalse(snap["closes_rt002"])
        self.assertFalse(snap["closes_rt003"])
        self.assertEqual(
            snap["kill_count"] + snap["hold_count"] + snap["accept_count"],
            len(TRIAGE_ROWS),
        )
        self.assertGreaterEqual(snap["kill_count"], 6)
        ids = {row["id"] for row in TRIAGE_ROWS}
        self.assertIn("RT-REMARK-LOC", ids)
        self.assertIn("RT-PACKS-SLA", ids)
        self.assertIn("RT-OOS-MANIFEST", ids)
        self.assertIn("RT-NODATA-SPEECH", ids)
        self.assertIn("RT-IFC-RAISE", ids)
        self.assertIn("RT-AXIS-NEAR", ids)
        self.assertIn("RT-CLOUD-OIDC", ids)
        self.assertIn("RT-002-SPPACK", ids)
        self.assertIn("RT-LIRA-SOLVER", ids)
        self.assertIn("RT-PDF-LIRA", ids)
        self.assertIn("RT-IFC-STREAM", ids)
        self.assertIn("RT-ZIP-SNIFF", ids)
        self.assertIn("RT-LIRA-HTTP", ids)
        self.assertIn("RT-SIDECAR-RTREE", ids)
        self.assertIn("RT-TYP-CATALOG", ids)
        self.assertIn("RT-PAGE-DRIFT", ids)
        self.assertIn("RT-CDE-IDENT", ids)

    def test_ids_unique_and_verdicts_known(self) -> None:
        ids = [row["id"] for row in TRIAGE_ROWS]
        self.assertEqual(len(ids), len(set(ids)))
        allowed = {"KILL", "HOLD", "ACCEPT"}
        for row in TRIAGE_ROWS:
            self.assertIn(row["verdict"], allowed)
            self.assertTrue(row["brake"])

    def test_v1_kill_brakes_are_wired(self) -> None:
        self.assertFalse(mik_act_may_cite_tz_v1_accuracy_as_measured())
        snap = v1_brief_snapshot()
        self.assertEqual(len(snap["paper_objects"]), 4)
        self.assertEqual(tuple(snap["paper_objects"]), PAPER_OBJECTS)
        self.assertFalse(snap["pdf"]["binary_in_git"])
        self.assertNotIn("pack_hash", snap)
        self.assertNotIn("customer_pack_hash", snap)
        self.assertEqual(snap["evaluation"]["pilot_interim_precision"], 0.60)

    def test_pass2_kt3_brakes_are_wired(self) -> None:
        from aerobim.domain.kt3_jury import Kt3JuryError, require_kt3_jury_gate
        from aerobim.domain.owner_files_inventory import (
            output_is_local_only,
            public_rehearsal_snapshot,
        )
        from aerobim.domain.signed_oos import evaluate_oos, unsigned_template
        from aerobim.domain.tracker_six_tasks import tracker_snapshot

        with self.assertRaises(Kt3JuryError):
            require_kt3_jury_gate(
                {
                    "passed": True,
                    "checkpoint_verdict": "NO_GO",
                    "findings": [
                        {
                            "rule_id": "IDS-Wall Fire Rating Multi",
                            "ifc_guid": "1XYVUKGoDDbREfVxRKsHkl",
                        }
                    ],
                }
            )
        snap = tracker_snapshot()
        self.assertFalse(snap["scheduled_demos_in_git"])
        self.assertGreaterEqual(snap["owner_blocked_count"], 4)
        self.assertEqual(snap["checkpoint"], "NO_GO")
        repo = Path(__file__).resolve().parents[2]
        self.assertFalse(output_is_local_only(repo, repo / "docs" / "evidence" / "leak.json"))
        rehearsal = public_rehearsal_snapshot()
        self.assertFalse(rehearsal["names_in_git"])
        self.assertFalse(rehearsal["hashes_in_git"])
        unsigned = evaluate_oos(unsigned_template("qto_space_area"))
        self.assertFalse(unsigned.licenses_unmeasured_speech)
        self.assertFalse(unsigned.closes_rt001)


if __name__ == "__main__":
    unittest.main()
