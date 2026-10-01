"""Open IFC header stress — fixture dir; GNI SKIPPED without env root."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_open_ifc_stress import (
    build_payload,
    detect_arc_structure_pairs,
    discover_ifc,
)

REPO = Path(__file__).resolve().parents[2]


class OpenIfcStressTests(unittest.TestCase):
    def test_discovers_repo_fixtures(self) -> None:
        found = discover_ifc(REPO / "samples" / "ifc")
        self.assertGreaterEqual(len(found), 10)

    def test_gni_skipped_when_root_missing(self) -> None:
        payload = build_payload(
            fixture_dir=REPO / "samples" / "ifc",
            gni_root=None,
            repo=REPO,
        )
        self.assertEqual(payload["gni"]["status"], "SKIPPED")
        self.assertGreaterEqual(payload["fixture"]["open_ok"], 10)
        self.assertEqual(payload["fixture"]["open_ok"], payload["fixture"]["file_count"])
        self.assertIn("content_sha256", payload)
        self.assertEqual(payload["gni"]["pairs_complete"], 0)

    def test_empty_dir_is_zero_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = build_payload(
                fixture_dir=Path(tmp),
                gni_root=None,
                repo=REPO,
            )
        self.assertEqual(payload["fixture"]["file_count"], 0)

    def test_detects_arc_structure_pairs(self) -> None:
        pairs = detect_arc_structure_pairs(
            [
                {"path": "2026_BIMprojects/model_0_arc.ifc", "bytes": 10, "schema": "IFC4"},
                {
                    "path": "2026_BIMprojects/model_0_structure.ifc",
                    "bytes": 11,
                    "schema": "IFC4",
                },
                {"path": "2026_BIMprojects/model_2_arc.ifc", "bytes": 12, "schema": "IFC4"},
            ]
        )
        by_stem = {pair["stem"]: pair for pair in pairs}
        self.assertTrue(by_stem["model_0"]["paired"])
        self.assertTrue(by_stem["model_0"]["schema_match"])
        self.assertFalse(by_stem["model_2"]["paired"])
        self.assertIn("arc_products", by_stem["model_0"])
        self.assertIn("structure_products", by_stem["model_0"])

    def test_header_only_does_not_read_whole_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            huge = root / "model_9_arc.ifc"
            header = b"ISO-10303-21;\nHEADER;\nFILE_SCHEMA(('IFC4'));\n"
            huge.write_bytes(header + (b"X" * (2 * 1024 * 1024)))
            payload = build_payload(fixture_dir=root, gni_root=root, repo=REPO)
        self.assertEqual(payload["gni"]["open_ok"], 1)
        self.assertEqual(payload["gni"]["file_count"], 1)


if __name__ == "__main__":
    unittest.main()
