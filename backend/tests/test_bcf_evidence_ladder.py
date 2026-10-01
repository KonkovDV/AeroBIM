"""Guard: BCF evidence ladder STATUS remains NOT_VERIFIED without inventing CDE proof."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CDE_PROOF = REPO_ROOT / "audit" / "evidence" / "cde-import-proof"
LADDER_DOC = REPO_ROOT / "docs" / "architecture" / "BCF_EVIDENCE_LADDER_T0_T4_2026_07.md"


class BcfEvidenceLadderTests(unittest.TestCase):
    def test_t2_status_gate_remains_not_verified(self) -> None:
        status_path = CDE_PROOF / "STATUS.json"
        self.assertTrue(status_path.is_file(), status_path)
        payload = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "NOT_VERIFIED")
        self.assertFalse(payload["claim_allowed"])
        self.assertEqual(payload.get("present_files"), [])
        self.assertIn("AVAILABLE", payload["allowed_wording"])
        self.assertIn("NOT_VERIFIED", payload["allowed_wording"])

    def test_t2_template_empty_and_ladder_doc_present(self) -> None:
        template_path = CDE_PROOF / "T2_EVIDENCE_TEMPLATE.json"
        self.assertTrue(template_path.is_file(), template_path)
        self.assertTrue(LADDER_DOC.is_file(), LADDER_DOC)
        template = json.loads(template_path.read_text(encoding="utf-8"))
        self.assertEqual(template["status"], "NOT_VERIFIED")
        self.assertFalse(template["claim_allowed"])
        self.assertEqual(template["artifacts"]["screenshot_or_pdf_path"], "")
        self.assertEqual(template["artifacts"]["import_log_path"], "")
        ladder = LADDER_DOC.read_text(encoding="utf-8")
        self.assertIn("T0", ladder)
        self.assertIn("T4", ladder)
        self.assertIn("NOT_VERIFIED", ladder)


if __name__ == "__main__":
    unittest.main()
