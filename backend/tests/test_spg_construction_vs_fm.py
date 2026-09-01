"""SPG Aug 2026 pin stays speech-only; PDFs stay off git; not SAM."""

from __future__ import annotations

import unittest
from pathlib import Path


class SpgConstructionVsFmPinTests(unittest.TestCase):
    def _md(self) -> str:
        repo = Path(__file__).resolve().parents[2]
        return (repo / "docs" / "quality" / "SPG_CONSTRUCTION_VS_FM_2026_09.md").read_text(
            encoding="utf-8"
        )

    def test_pin_stays_no_go_and_splits_markets(self) -> None:
        md = self._md()
        self.assertIn("NO_GO", md)
        self.assertIn("398-р", md)
        self.assertIn("FM/PM", md)
        self.assertIn("не в git", md)
        self.assertNotIn("пакет обработан", md)
        self.assertNotIn("DWG-ready", md)
        self.assertNotIn("81 ГиБ", md)

    def test_tier0_omits_consulting_pdf_pin(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        text = (repo / "docs" / "TIER0_INDEX.md").read_text(encoding="utf-8")
        self.assertNotIn("SPG_CONSTRUCTION_VS_FM_2026_09.md", text)


if __name__ == "__main__":
    unittest.main()
