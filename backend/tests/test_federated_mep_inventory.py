"""Federated MEP inventory stays NOT_VERIFIED."""

from __future__ import annotations

import unittest
from pathlib import Path

from aerobim.tools.run_federated_mep_inventory import build_payload

REPO = Path(__file__).resolve().parents[2]


class FederatedMepInventoryTests(unittest.TestCase):
    def test_fixture_present_and_not_delivered(self) -> None:
        payload = build_payload(repo=REPO)
        self.assertEqual(payload["mep_system_clash"], "NOT_VERIFIED")
        self.assertFalse(payload["closes_rt003"])
        self.assertGreaterEqual(payload["present"], 1)
        labels = {row["label"]: row["status"] for row in payload["rows"]}
        self.assertEqual(labels["eng_fixture"], "RUN")


if __name__ == "__main__":
    unittest.main()
