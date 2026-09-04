
"""KT#3 jury gate picks a GUID finding and stays fail-closed."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.kt3_jury import Kt3JuryError, require_kt3_jury_gate, select_jury_finding
from aerobim.tools.run_kt3_jury import assemble_kt3_jury
from aerobim.tools.run_kt3_jury import main as jury_main

_REPO = Path(__file__).resolve().parents[2]


def _gate(*, passed: bool = False, findings: list[dict] | None = None) -> dict:
    return {
        "passed": passed,
        "checkpoint_verdict": CHECKPOINT,
        "finding_count": 2,
        "capabilities": {"mep_system_clash": "NOT_VERIFIED"},
        "findings": findings
        or [
            {"rule_id": "REQ-AREA-1", "ifc_guid": None, "expected": "10", "observed": "9"},
            {
                "finding_id": "ids-wall",
                "rule_id": "IDS-Wall Fire Rating Multi",
                "ifc_guid": "1XYVUKGoDDbREfVxRKsHkl",
                "expected": "REI60",
                "observed": "REI30",
            },
        ],
    }


class Kt3JuryTests(unittest.TestCase):
    def test_selects_guid_finding_not_area_null(self) -> None:
        picked = select_jury_finding(_gate()["findings"])
        self.assertEqual(picked["rule_id"], "IDS-Wall Fire Rating Multi")
        self.assertEqual(picked["ifc_guid"], "1XYVUKGoDDbREfVxRKsHkl")
        self.assertEqual(picked["expected"], "REI60")
        self.assertEqual(picked["observed"], "REI30")

    def test_parses_expected_observed_from_ids_remark(self) -> None:
        picked = select_jury_finding(
            [
                {
                    "rule_id": "IDS-Wall Fire Rating Multi",
                    "ifc_guid": "1XYVUKGoDDbREfVxRKsHkl",
                    "expected": None,
                    "observed": None,
                    "remark": (
                        "Property — FireRating data shall be REI60 "
                        '(The property value "REI30" does not match the requirements).'
                    ),
                }
            ]
        )
        self.assertEqual(picked["expected"], "REI60")
        self.assertEqual(picked["observed"], "REI30")

    def test_passed_true_is_rejected(self) -> None:
        with self.assertRaises(Kt3JuryError):
            require_kt3_jury_gate(_gate(passed=True))

    def test_mep_ok_is_rejected(self) -> None:
        gate = _gate()
        gate["capabilities"] = {"mep_system_clash": "OK"}
        with self.assertRaises(Kt3JuryError):
            require_kt3_jury_gate(gate)

    def test_assemble_keeps_tracker_and_typical_errors(self) -> None:
        payload = assemble_kt3_jury(_REPO, gate=_gate(), generated_at="2026-08-27T00:00:00+00:00")
        self.assertEqual(payload["checkpoint"], CHECKPOINT)
        self.assertFalse(payload["passed"])
        self.assertEqual(payload["typical_errors"]["customer_confirmed_patterns"], 0)
        self.assertGreaterEqual(payload["typical_errors"]["pattern_count"], 20)
        self.assertEqual(payload["tracker"]["item_count"], 6)
        self.assertEqual(payload["tracker_eight"]["item_count"], 8)
        self.assertEqual(payload["tracker_eight"]["auth_bff_status"], "NOT_IMPLEMENTED")
        self.assertEqual(len(payload["paper_objects"]), 4)
        self.assertFalse(payload["nda_corpus_in_git"])

    def test_cli_skip_demo_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate_path = Path(tmp) / "gate.json"
            gate_path.write_text(json.dumps(_gate()), encoding="utf-8")
            code = jury_main(
                [
                    "--skip-demo",
                    "--gate-json",
                    str(gate_path),
                    "--generated-at",
                    "2026-08-27T00:00:00+00:00",
                ]
            )
        self.assertEqual(code, 0)
        latest = _REPO / "artifacts" / "kt3-jury" / "latest.json"
        self.assertTrue(latest.is_file())
        payload = json.loads(latest.read_text(encoding="utf-8"))
        self.assertFalse(payload["passed"])
        self.assertEqual(payload["jury_finding"]["ifc_guid"], "1XYVUKGoDDbREfVxRKsHkl")
        pack_path = _REPO / "artifacts" / "kt3-without-customer" / "latest.json"
        self.assertTrue(pack_path.is_file())
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        self.assertEqual(pack["schema_version"], "1.6.0")
        self.assertFalse(pack["closes_rt001"])


if __name__ == "__main__":
    unittest.main()
