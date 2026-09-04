"""Live product checkpoint is GO (regulatory MVP); customer_go stays false."""

from __future__ import annotations

import unittest

from aerobim.domain.checkpoint import (
    CHECKPOINT,
    CUSTOMER_GO,
    GO_KIND,
    CheckpointHonestyError,
    checkpoint_fields,
    require_honest_checkpoint,
)


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


if __name__ == "__main__":
    unittest.main()
