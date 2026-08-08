"""Lock BSI IDS case 0017 as a known IfcTester upstream edge (not product accuracy)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[2]
CASE_DIR = REPO / "samples" / "ids" / "buildingsmart-testcases" / "cases" / "0017"
EDGE_REGISTRY = (
    REPO / "samples" / "ids" / "buildingsmart-testcases" / "KNOWN_UPSTREAM_EDGES.json"
)


class IdsCase0017UpstreamEdgeTests(unittest.TestCase):
    def test_registry_lists_0017(self) -> None:
        payload = json.loads(EDGE_REGISTRY.read_text(encoding="utf-8"))
        edges = payload["edges"]
        self.assertTrue(any(e.get("case_dir") == "0017" for e in edges))
        match = next(e for e in edges if e["case_dir"] == "0017")
        self.assertEqual(match["bsi_filename_expected"], "pass")
        self.assertEqual(match["ifctester_observed"], "fail")
        self.assertEqual(match["classification"], "upstream_ids_ifctester_edge")
        self.assertIn("Do not patch", match["aerobim_action"])

    def test_ifctester_adapter_fails_optional_null_name(self) -> None:
        from aerobim.infrastructure.adapters.ifc_tester_ids_validator import (
            IfcTesterIdsValidator,
        )

        ids_path = CASE_DIR / "pass-an_optional_attribute_passes_if_null.ids"
        ifc_path = CASE_DIR / "pass-an_optional_attribute_passes_if_null.ifc"
        self.assertTrue(ids_path.exists())
        self.assertTrue(ifc_path.exists())

        try:
            issues = IfcTesterIdsValidator().validate(ids_path, ifc_path)
        except Exception as exc:  # noqa: BLE001 — XSD fetch / ifctester env flake
            message = f"{type(exc).__name__}: {exc}".lower()
            networkish = any(
                token in message
                for token in (
                    "urlerror",
                    "incompleteread",
                    "timed out",
                    "connection",
                    "http",
                    "ssl",
                    "getaddrinfo",
                    "xmlschema",
                    "schema",
                )
            )
            if networkish:
                self.skipTest(f"IfcTester/XSD environment unavailable: {exc}")
            raise

        # BSI filename says pass; IfcTester 0.8.x fails — lock the edge, do not greenwash.
        self.assertGreater(len(issues), 0, "expected IfcTester fail on optional null Name")
        joined = " ".join(i.message for i in issues).lower()
        self.assertTrue(
            "empty" in joined or "none" in joined or "name" in joined,
            f"unexpected failure message(s): {[i.message for i in issues]}",
        )


if __name__ == "__main__":
    unittest.main()
