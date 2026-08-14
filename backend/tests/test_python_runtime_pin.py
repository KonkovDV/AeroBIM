"""CI / clone interpreter pin is CPython 3.12 (not a product-accuracy claim)."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class PythonRuntimePinTests(unittest.TestCase):
    def test_python_version_file_pins_3_12(self) -> None:
        text = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
        self.assertEqual(text, "3.12")

    def test_ci_runs_cpython_3_12(self) -> None:
        if os.environ.get("GITHUB_ACTIONS") != "true" and os.environ.get("CI") != "true":
            self.skipTest("local venv may be 3.13; CI pin is 3.12")
        self.assertEqual(
            sys.version_info[:2],
            (3, 12),
            "CI python-version must stay 3.12",
        )


if __name__ == "__main__":
    unittest.main()
