"""Inventory guard for pilot threat-model / security control surfaces."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class PilotThreatModelInventoryTests(unittest.TestCase):
    def test_threat_model_and_key_security_modules_exist(self) -> None:
        threat_model = REPO_ROOT / "docs" / "security" / "PILOT_THREAT_MODEL_2026_07.md"
        self.assertTrue(threat_model.is_file(), threat_model)
        text = threat_model.read_text(encoding="utf-8")
        self.assertIn("POST-05", text)
        self.assertIn("NOT_IMPLEMENTED", text)
        self.assertIn("Does not claim SSO production-ready", text)
        self.assertNotIn("SSO is production-ready", text)

        required = [
            REPO_ROOT / "backend" / "tests" / "test_api_security.py",
            REPO_ROOT / "backend" / "tests" / "test_rt_phase4_security.py",
            REPO_ROOT / "backend" / "tests" / "test_upload_content_security.py",
            REPO_ROOT / "backend" / "tests" / "test_rt_remediation_post.py",
            REPO_ROOT / "backend" / "tests" / "test_rtatom_remediation_2026_07_20.py",
            REPO_ROOT / "backend" / "tests" / "test_rtatom_wave_a3_2026_07_20.py",
            REPO_ROOT / "docs" / "architecture" / "POST05_OIDC_BFF_DESIGN_2026_07.md",
            REPO_ROOT / "SECURITY.md",
        ]
        for path in required:
            self.assertTrue(path.is_file(), path)


if __name__ == "__main__":
    unittest.main()
