"""Customer pack bytes and PII must stay out of git."""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    git = shutil.which("git")
    if not git:
        raise unittest.SkipTest("git executable not found")
    return subprocess.run([git, *args], cwd=_REPO, check=True, capture_output=True)


class CustomerDataNotInGitTests(unittest.TestCase):
    def test_samples_customer_only_readme(self) -> None:
        proc = _git("ls-files", "-z", "samples/customer")
        paths = [part.replace("\\", "/") for part in proc.stdout.decode().split("\0") if part]
        self.assertTrue(all(path.endswith("README.md") for path in paths), paths)

    def test_files_tree_is_not_tracked(self) -> None:
        proc = _git("ls-files", "-z", "files")
        self.assertEqual(proc.stdout.decode().strip("\0"), "")

    def test_ingest_fixture_pii_not_committed(self) -> None:
        git = shutil.which("git")
        if not git:
            raise unittest.SkipTest("git executable not found")
        tracked = subprocess.run(
            [git, "grep", "-I", "-n", "ivanov@example.com"],
            cwd=_REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        hits = [
            line
            for line in (tracked.stdout or "").splitlines()
            if "backend/tests/" not in line.replace("\\", "/")
        ]
        self.assertEqual(hits, [])
        self.assertTrue(_EMAIL_RE.search("ivanov@example.com"))


if __name__ == "__main__":
    unittest.main()
