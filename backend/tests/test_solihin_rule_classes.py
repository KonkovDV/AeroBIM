from __future__ import annotations

import unittest

from aerobim.tools.export_solihin_rule_classes import (
    build_solihin_inventory,
    classify_rule,
    render_solihin_markdown,
)


class SolihinRuleClassTests(unittest.TestCase):
    def test_prefix_classes(self) -> None:
        self.assertEqual(classify_rule("AEROBIM-PACKAGE-MISSING-SECTION")[0], 1)
        self.assertEqual(classify_rule("AEROBIM-QTY-ERROR")[0], 2)
        self.assertEqual(classify_rule("AEROBIM-CLASH-CAPABILITY")[0], 3)
        self.assertEqual(classify_rule("AEROBIM-AGENT-IDS-DRAFT")[0], 4)
        self.assertEqual(classify_rule("UNKNOWN-RULE")[0], 0)

    def test_inventory_keeps_class_4_unclaimed(self) -> None:
        payload = build_solihin_inventory()
        self.assertTrue(payload["class_4_not_claimed"])
        self.assertGreater(payload["summary"]["rule_count"], 20)
        self.assertGreaterEqual(payload["summary"]["class_1_explicit"], 1)
        md = render_solihin_markdown(payload)
        self.assertIn("not claimed", md)
        self.assertIn("content_sha256", md)


if __name__ == "__main__":
    unittest.main()
