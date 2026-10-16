"""AER-03: the configured per-test timeout must turn a hang into a failure."""

from __future__ import annotations

import subprocess
import sys
import textwrap
import tomllib
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


class PytestTimeoutGuardTest(unittest.TestCase):
    def test_pyproject_timeout_is_60_seconds(self) -> None:
        cfg = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
        ini = cfg["tool"]["pytest"]["ini_options"]
        self.assertEqual(ini["timeout"], 60)
        self.assertTrue(any(m.startswith("network:") for m in ini["markers"]))

    def test_hanging_test_fails_on_timeout(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            ini = Path(tmp) / "pytest.ini"
            ini.write_text("[pytest]\n", encoding="utf-8")
            probe = Path(tmp) / "test_hang_probe.py"
            probe.write_text(
                textwrap.dedent(
                    """
                    import time

                    def test_hangs():
                        time.sleep(30)
                    """
                ),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "-c",
                    str(ini),
                    "--timeout=2",
                    str(probe),
                ],
                capture_output=True,
                text=True,
                timeout=25,
                cwd=tmp,
            )
        out = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, out)
        self.assertIn("Timeout", out)
        self.assertIn("test_hangs", out)


if __name__ == "__main__":
    unittest.main()
