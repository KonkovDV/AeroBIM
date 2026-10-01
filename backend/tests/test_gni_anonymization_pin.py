"""GNI anonymization scripts are pinned, not rewritten."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.export_gni_anonymization_pin import EXPECTED_SCRIPTS, build_payload

REPO = Path(__file__).resolve().parents[2]


class GniAnonymizationPinTests(unittest.TestCase):
    def test_skipped_without_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_payload(code_root=Path(tmp) / "missing", repo=REPO)
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertEqual(payload["execution"], "SKIPPED")
        self.assertIn("content_sha256", payload)

    def test_pinned_when_scripts_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "code").mkdir()
            for rel in EXPECTED_SCRIPTS:
                path = root / rel
                path.write_text("MIT pin fixture\n", encoding="utf-8")
            payload = build_payload(code_root=root, repo=REPO)
        self.assertEqual(payload["status"], "PINNED")
        self.assertEqual(len(payload["files"]), 3)
        self.assertTrue(all(item["present"] for item in payload["files"]))


if __name__ == "__main__":
    unittest.main()
