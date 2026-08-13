"""MOEXP-on-GNI sample is SKIPPED without the gitignored IFC."""

from __future__ import annotations

import unittest

from aerobim.tools.run_moexp_on_gni_sample import skipped_payload


class MoexpOnGniSampleTests(unittest.TestCase):
    def test_skipped_payload_is_not_compliance(self) -> None:
        payload = skipped_payload(reason="missing")
        self.assertEqual(payload["status"], "SKIPPED")
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertIn("content_sha256", payload)


if __name__ == "__main__":
    unittest.main()
