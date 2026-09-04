"""IFC Acceptance Gate demo CLI — fixture path without overlay sidecar."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.tools.run_demo_ifc_acceptance_gate import run_demo_ifc_acceptance_gate


class DemoIfcAcceptanceGateTests(unittest.TestCase):
    def test_end_to_end_writes_gate_html_json_bcf_without_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            gate = run_demo_ifc_acceptance_gate(output_dir=out)
            self.assertFalse(gate["passed"])
            self.assertEqual(gate["checkpoint_verdict"], CHECKPOINT)
            self.assertGreaterEqual(gate["finding_count"], 1)
            self.assertTrue((out / "acceptance-gate.json").is_file())
            self.assertTrue((out / "report.html").is_file())
            self.assertTrue((out / "report.json").is_file())
            self.assertTrue((out / "findings.bcfzip").is_file())
            self.assertFalse((out / "overlay-problem-zone.png").is_file())
            payload = json.loads((out / "acceptance-gate.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_type"], "aerobim_ifc_acceptance_gate")
            self.assertEqual(payload["schema_version"], "1.1.0")
            self.assertEqual(payload["outcome_scope"], "full_package")
            self.assertEqual(payload["findings_scope"], "ifc_ids")
            self.assertIn("blocking_outside_projection_count", payload)
            self.assertIn("ids_validation", payload["capabilities"])
            self.assertTrue(payload["findings"][0]["rule_id"])


if __name__ == "__main__":
    unittest.main()
