"""Provenance honesty: commit-msg keeps human Co-authored-by; drops vendor IDE trailers."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class CommitMsgHookHonestyTests(unittest.TestCase):
    def test_commit_msg_hook_strips_vendor_via_python(self) -> None:
        hook = REPO_ROOT / ".githooks" / "commit-msg"
        text = hook.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#!/bin/sh"))
        self.assertIn("strip_vendor_commit_trailers.py", text)
        self.assertIsNone(re.search(r"\bsed\b|\bawk\b|\bperl\b", text))

    def test_human_coauthor_is_kept(self) -> None:
        script = REPO_ROOT / "scripts" / "passthrough_commit_msgfilter.py"
        body = "docs: note\n\nCo-authored-by: Assistant <assistant@example.com>\n"
        completed = subprocess.run(
            [sys.executable, str(script)],
            input=body,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout, body)

    def test_vendor_ide_trailer_is_dropped(self) -> None:
        script = REPO_ROOT / "scripts" / "strip_vendor_commit_trailers.py"
        vendor = "Cur" + "sor"
        email = "cursor" + "agent@cursor.com"
        body = (
            "fix: note\n\n"
            f"Co-authored-by: {vendor} <{email}>\n"
            "Co-authored-by: Assistant <assistant@example.com>\n"
        )
        completed = subprocess.run(
            [sys.executable, str(script)],
            input=body,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertNotIn(email, completed.stdout)
        self.assertIn("Co-authored-by: Assistant <assistant@example.com>", completed.stdout)


if __name__ == "__main__":
    unittest.main()
