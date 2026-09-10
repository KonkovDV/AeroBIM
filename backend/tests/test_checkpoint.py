"""Live product checkpoint is GO (regulatory MVP); customer_go stays false."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import (
    CHECKPOINT,
    CUSTOMER_GO,
    GO_KIND,
    CheckpointHonestyError,
    checkpoint_fields,
    require_honest_checkpoint,
)

_REPO = Path(__file__).resolve().parents[2]


class CheckpointSotTests(unittest.TestCase):
    def test_go_is_regulatory_mvp_not_customer_signoff(self) -> None:
        self.assertEqual(CHECKPOINT, "GO")
        self.assertEqual(GO_KIND, "regulatory_measurement_mvp")
        self.assertFalse(CUSTOMER_GO)
        fields = checkpoint_fields()
        self.assertEqual(fields["checkpoint"], "GO")
        self.assertFalse(fields["customer_go"])
        self.assertFalse(fields["market_go"])
        self.assertFalse(fields["deployment_go"])

    def test_customer_go_true_is_rejected(self) -> None:
        dirty = checkpoint_fields()
        dirty["customer_go"] = True
        with self.assertRaises(CheckpointHonestyError):
            require_honest_checkpoint(dirty)

    def test_omitted_customer_go_is_rejected(self) -> None:
        with self.assertRaises(CheckpointHonestyError):
            require_honest_checkpoint({"checkpoint": "GO"})

    def test_no_go_payload_is_rejected_on_live_ssot(self) -> None:
        with self.assertRaises(CheckpointHonestyError):
            require_honest_checkpoint({"checkpoint": "NO_GO", "customer_go": False})


class LiveInjectionPinTests(unittest.TestCase):
    """Historical 03.09 pins: wording and denominator only. Do not hand-edit checkpoint."""

    def test_channel_latest_pin_is_output_sensitivity_proxy(self) -> None:
        payload = json.loads(
            (_REPO / "docs/evidence/defect-injection-recall-run-latest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["git_commit"], "929a787a8972daffc9d39638163fa5338f62543b")
        self.assertEqual(payload["aggregate"]["killed"], 0)
        self.assertEqual(payload["aggregate"]["trials"], 6)
        self.assertEqual(payload["aggregate"]["recall_point"], 0.0)
        self.assertAlmostEqual(payload["aggregate"]["wilson_95"]["upper"], 0.390334)
        self.assertEqual(
            sorted(payload["not_applied_classes"]),
            ["IDS_VIOLATION", "MISSING_ELEMENT"],
        )
        self.assertEqual(payload["determinism_check"]["status"], "pass")
        self.assertEqual(payload["control_issue_count"], 97)
        self.assertIn("not seam-clean", payload["plan_deviation"])
        self.assertFalse(payload["closes_rt001"])

    def test_fixture_latest_pin_keeps_synthetic_denominator(self) -> None:
        payload = json.loads(
            (_REPO / "docs/evidence/defect-injection-recall-run-fixture-latest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["aggregate"]["trials"], 8)
        self.assertEqual(payload["aggregate"]["killed"], 1)
        self.assertFalse(payload["closes_rt001"])


if __name__ == "__main__":
    unittest.main()
