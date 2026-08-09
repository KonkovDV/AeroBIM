"""Provenance honesty: commit-msg must not strip Co-authored-by (N-34 / A-3)."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class CommitMsgHookHonestyTests(unittest.TestCase):
    def test_commit_msg_hook_is_passthrough(self) -> None:
        hook = REPO_ROOT / ".githooks" / "commit-msg"
        text = hook.read_text(encoding="utf-8")
        code_lines = [
            line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(text.startswith("#!/bin/sh"))
        self.assertEqual(code_lines, ["exit 0"])
        self.assertIsNone(re.search(r"\bsed\b|\bawk\b|\bperl\b", text))

    def test_strip_filter_is_passthrough(self) -> None:
        script = REPO_ROOT / "scripts" / "strip_coauthor_msgfilter.py"
        body = "docs: note\n\nCo-authored-by: Assistant <assistant@example.com>\n"
        completed = subprocess.run(
            ["python", str(script)],
            input=body,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout, body)


if __name__ == "__main__":
    unittest.main()
