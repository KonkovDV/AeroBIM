"""Guard: open-core ADR exists and LICENSE was not altered by ADR-002."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class OpenCoreAdrTests(unittest.TestCase):
    def test_adr_002_present_without_license_change_claim(self) -> None:
        adr = REPO_ROOT / "docs" / "architecture" / "ADR-002-open-core-commercial-boundary-2026.md"
        license_path = REPO_ROOT / "LICENSE"
        self.assertTrue(adr.is_file(), adr)
        self.assertTrue(license_path.is_file(), license_path)
        text = adr.read_text(encoding="utf-8")
        license_text = license_path.read_text(encoding="utf-8")
        self.assertIn("MIT", text)
        self.assertIn("without changing the LICENSE", text)
        self.assertIn("MIT License", license_text)
        self.assertIn("2026", license_text)


if __name__ == "__main__":
    unittest.main()
