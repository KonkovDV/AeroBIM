"""Demo acceptance-gate remarks cite demo TZ and spatial index (п. 2.1.5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_demo_ifc_acceptance_gate import run_demo_ifc_acceptance_gate

_UNBOUND = "пункт нормы не привязан"
_NO_SPATIAL = "нет в пространственном индексе"
# Majority of jury-visible findings must carry a real demo-TZ clause and
# must not show the spatial-index fallback on GUID rows.
_FILL_FLOOR = 0.6


class DemoRemarkFillTests(unittest.TestCase):
    def test_acceptance_gate_majority_have_clause_and_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = run_demo_ifc_acceptance_gate(output_dir=Path(tmp))
        findings = gate.get("findings") or []
        self.assertGreaterEqual(len(findings), 1)
        bound = 0
        located = 0
        guid_rows = 0
        guid_spatial = 0
        for item in findings:
            if not isinstance(item, dict):
                continue
            remark = str(item.get("remark") or "")
            if _UNBOUND not in remark:
                bound += 1
            if _NO_SPATIAL not in remark:
                located += 1
            if item.get("ifc_guid"):
                guid_rows += 1
                if _NO_SPATIAL not in remark:
                    guid_spatial += 1
        n = len(findings)
        self.assertGreaterEqual(bound / n, _FILL_FLOOR, msg=f"bound={bound}/{n}")
        self.assertGreaterEqual(located / n, _FILL_FLOOR, msg=f"located={located}/{n}")
        self.assertGreaterEqual(guid_rows, 1)
        self.assertEqual(guid_spatial, guid_rows)
