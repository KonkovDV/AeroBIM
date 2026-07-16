from __future__ import annotations

import unittest

from aerobim.domain.architecture import (
    PrecisionClaim,
    precision_claim_publishable_with_agreement,
)
from aerobim.domain.system_capabilities import (
    build_system_capabilities_payload,
    load_customer_intake_gate_snapshot,
)


class PrecisionAgreementPublishabilityTests(unittest.TestCase):
    def test_customer_claim_requires_agreement_when_required(self) -> None:
        claim = PrecisionClaim(
            metric="macro_precision",
            value=0.91,
            corpus_id="customer-1",
            corpus_kind="customer",
            adjudicators=2,
            date="2026-07-17",
        )
        self.assertTrue(claim.publishable)
        self.assertFalse(
            precision_claim_publishable_with_agreement(
                claim, agreement=None, require_agreement=True
            )
        )
        self.assertTrue(
            precision_claim_publishable_with_agreement(
                claim,
                agreement={
                    "pass_threshold_0_60": True,
                    "pass_alpha_0_67": True,
                    "krippendorff_alpha": 0.8,
                },
                require_agreement=True,
            )
        )
        self.assertFalse(
            precision_claim_publishable_with_agreement(
                claim,
                agreement={"pass_threshold_0_60": False, "pass_alpha_0_67": True},
                require_agreement=True,
            )
        )

    def test_capabilities_include_intake_gate_no_go(self) -> None:
        payload = build_system_capabilities_payload()
        self.assertEqual(payload["schema_version"], "1.1.0")
        intake = payload["customer_intake_gate"]
        assert isinstance(intake, dict)
        self.assertEqual(intake["checkpoint"], "NO_GO")
        self.assertIn("precision_claim", payload["claim_boundary"])
        snap = load_customer_intake_gate_snapshot()
        self.assertEqual(snap["checkpoint"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
