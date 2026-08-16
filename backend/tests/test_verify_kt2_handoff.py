from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.verify_evidence_bundle import verify_evidence_bundle
from aerobim.tools.verify_kt2_handoff import verify_kt2_handoff

_REPO = Path(__file__).resolve().parents[2]


class VerifyKt2HandoffTests(unittest.TestCase):
    def test_current_handoff_pack_is_green_and_no_go(self) -> None:
        handoff = _REPO / "docs" / "evidence" / "kt2-handoff-2026-08-11"
        if not (handoff / "STATUS.json").is_file():
            self.skipTest("KT#2 handoff pack missing")
        result = verify_kt2_handoff(handoff_dir=handoff, repo=_REPO)
        self.assertTrue(result["ok"], msg=result)
        self.assertEqual(result["checkpoint_verdict"], "NO_GO")
        names = {c["check"] for c in result["checks"]}
        self.assertIn("clash_precision_not_customer", names)
        clash_pr = next(c for c in result["checks"] if c["check"] == "clash_precision_not_customer")
        self.assertTrue(clash_pr["ok"], msg=clash_pr)
        failed = [c for c in result["checks"] if not c["ok"]]
        self.assertEqual(failed, [])
        self.assertIn("rehearsal_forbids_wall_guid_html", names)
        self.assertIn("handoff_readme_live_cli", names)
        self.assertIn("snapshot_html_not_overlay_demo", names)
        self.assertIn("readme_quickstart_demo_core_pdf", names)
        self.assertIn("kt2_video_script", names)
        self.assertIn("kt2_demo_mp4_not_in_docs", names)
        mp4 = next(c for c in result["checks"] if c["check"] == "kt2_demo_mp4_status")
        self.assertTrue(mp4["ok"])
        self.assertIn(mp4["detail"], {"NOT_IN_GIT", "PRESENT_LOCAL_NOT_IN_GIT"})

    def test_wall_guid_snapshot_is_lf_and_verifies(self) -> None:
        wall = _REPO / "docs" / "evidence" / "kt2-handoff-2026-08-11" / "wall-guid"
        if not (wall / "manifest.json").is_file():
            self.skipTest("wall-guid snapshot missing")
        for path in wall.iterdir():
            if path.is_file():
                self.assertNotIn(b"\r\n", path.read_bytes(), msg=path.name)
        result = verify_evidence_bundle(wall)
        self.assertTrue(result["ok"], msg=result)


if __name__ == "__main__":
    unittest.main()
