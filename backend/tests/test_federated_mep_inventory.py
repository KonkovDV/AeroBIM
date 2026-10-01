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
        self.assertIn("hvac_fixture_graph_aabb", payload["geometry"])
        self.assertEqual(payload["geometry"]["hvac_fixture_graph_aabb"]["geometry_verified"], False)
        self.assertEqual(payload["geometry"]["hvac_fixture_graph_aabb"]["status"], "RUN")
        self.assertIn("duplex_arc_mep_aabb", payload["geometry"])
        self.assertFalse(payload["geometry"]["duplex_arc_mep_aabb"]["geometry_verified"])


if __name__ == "__main__":
    unittest.main()
