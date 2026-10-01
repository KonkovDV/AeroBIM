"""CLI catalog and shared helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools._cli_base import add_common_args, output_json
from aerobim.tools.tool_catalog import catalog


class ToolCatalogTests(unittest.TestCase):
    def test_catalog_groups_include_core_and_sprint(self) -> None:
        groups = catalog()
        self.assertIn("validate_dwg_toolchain", groups["core"])
        self.assertIn("run_demo_vertical_slice", groups["core"])
        self.assertIn("run_demo_ifc_acceptance_gate", groups["core"])
        self.assertIn("run_demo_path", groups["sprint_archive"])
        self.assertIn("run_sprint2_synthetic_baseline", groups["sprint_archive"])
        self.assertTrue(groups["evaluate"])
        self.assertTrue(groups["export"])
        active = __import__("aerobim.tools.tool_catalog", fromlist=["active_tools"]).active_tools()
        self.assertLessEqual(len(active), 40)
        self.assertIn("validate_dwg_toolchain", active)
        self.assertIn("run_demo_vertical_slice", active)
        self.assertIn("run_demo_ifc_acceptance_gate", active)
        self.assertNotIn("run_demo_path", active)
        self.assertNotIn("export_sprint2_dataset_manifest", active)

    def test_output_json_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            output_json({"ok": True}, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])

    def test_add_common_args(self) -> None:
        import argparse

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--json", "--verbose"])
        self.assertTrue(args.json)
        self.assertTrue(args.verbose)


if __name__ == "__main__":
    unittest.main()
