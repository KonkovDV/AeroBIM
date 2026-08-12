from __future__ import annotations

import unittest
from pathlib import Path

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
        failed = [c for c in result["checks"] if not c["ok"]]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
