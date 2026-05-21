"""Tests for Samolet typical-error mapping tool."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.tools.map_typical_errors import default_catalog_path, map_typical_errors


class MapTypicalErrorsTests(unittest.TestCase):
    def test_catalog_maps_fire_and_structure_prefixes(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        payload = map_typical_errors(
            default_catalog_path(),
            repo_root / "samples" / "requirements",
        )
        self.assertEqual(payload["artifact_type"], "samolet_typical_errors_mapping")
        self.assertGreaterEqual(payload["patterns_with_rule_match"], 3)
        rows = payload["rows"]
        fire_row = next(r for r in rows if r["error_id"] == "SAM-TYP-001")
        self.assertEqual(fire_row["status"], "covered")
        self.assertTrue(fire_row["matched_rule_ids"])

    def test_cli_writes_json(self) -> None:
        import tempfile

        from aerobim.tools.map_typical_errors import main

        repo_root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mapping.json"
            import sys

            old_argv = sys.argv
            try:
                sys.argv = [
                    "map_typical_errors",
                    "--catalog",
                    str(default_catalog_path()),
                    "--rules-dir",
                    str(repo_root / "samples" / "requirements"),
                    "--output",
                    str(out),
                ]
                main()
            finally:
                sys.argv = old_argv
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("coverage_ratio", data)


if __name__ == "__main__":
    unittest.main()
