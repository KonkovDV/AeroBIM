"""Windows hashed lock, Dev Container, and engine-strict stay honest."""

from __future__ import annotations

import json
import unittest

from aerobim.tools.offline_bundle import _BUNDLE_FILES
from aerobim.tools.seed_smoke_report import repo_root


class WindowsLockAndDevContainerTests(unittest.TestCase):
    def test_windows_lock_omits_uvloop_and_pymupdf(self) -> None:
        text = (repo_root() / "backend" / "requirements-win-lock.txt").read_text(encoding="utf-8")
        lower = text.lower()
        self.assertNotIn("uvloop==", lower)
        self.assertNotIn("pymupdf==", lower)
        self.assertIn("ifcopenshell==", lower)
        self.assertIn("colorama==", lower)
        self.assertIn("x86_64-pc-windows-msvc", text)
        self.assertIn("--extra=dev", text)
        self.assertIn("--extra=raster", text)
        self.assertNotIn("pdf-agpl", text)

    def test_linux_runtime_lock_still_has_uvloop(self) -> None:
        text = (repo_root() / "backend" / "requirements-lock.txt").read_text(encoding="utf-8")
        self.assertIn("uvloop==", text.lower())

    def test_windows_lock_is_not_the_offline_bundle(self) -> None:
        self.assertNotIn("requirements-win-lock.txt", _BUNDLE_FILES)

    def test_devcontainer_is_contributor_not_jury(self) -> None:
        root = repo_root()
        payload = json.loads(
            (root / ".devcontainer" / "devcontainer.json").read_text(encoding="utf-8")
        )
        self.assertEqual(payload["forwardPorts"], [8080, 5173])
        self.assertEqual(payload["remoteEnv"]["AEROBIM_ENV"], "development")
        self.assertNotIn("AEROBIM_SIGNOFF_PROFILE", payload["remoteEnv"])
        self.assertEqual(payload["portsAttributes"]["3000"]["onAutoForward"], "ignore")
        self.assertIn("3.12", payload["image"])
        setup = (root / ".devcontainer" / "post-create.sh").read_text(encoding="utf-8")
        self.assertIn('".[dev,raster]"', setup)
        self.assertNotIn("pdf-agpl", setup)
        self.assertNotIn("export AEROBIM_SIGNOFF", setup)
        self.assertIn("run_kt3_jury", setup)
        readme = (root / ".devcontainer" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Not the jury CLI", readme)
        self.assertIn("customer_go", readme)


if __name__ == "__main__":
    unittest.main()
