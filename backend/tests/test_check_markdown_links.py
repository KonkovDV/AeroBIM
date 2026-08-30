"""Relative markdown links in jury trees resolve; K3 ticksheet stays in quality/."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.check_markdown_links import check_links

_REPO = Path(__file__).resolve().parents[2]
_JURY_PREFIXES = (
    "docs/quality/",
    "docs/partners/",
    "docs/demo/",
    "docs/evidence/",
)


class CheckMarkdownLinksTests(unittest.TestCase):
    def test_evidence_map_k3_ticksheet_is_not_under_partners(self) -> None:
        text = (_REPO / "docs" / "quality" / "MIK_CRITERION_EVIDENCE_MAP_2026_08.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("](K3_PARTNER_FIT_TICKSHEET_2026_08.md)", text)
        self.assertNotIn(
            "](../partners/K3_PARTNER_FIT_TICKSHEET_2026_08.md)",
            text,
        )
        ticksheet = _REPO / "docs" / "quality" / "K3_PARTNER_FIT_TICKSHEET_2026_08.md"
        self.assertTrue(ticksheet.is_file())

    def test_jury_trees_have_no_broken_relative_links(self) -> None:
        errors = [
            item
            for item in check_links(_REPO)
            if any(prefix in item.replace("\\", "/") for prefix in _JURY_PREFIXES)
        ]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
