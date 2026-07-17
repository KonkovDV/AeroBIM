"""Protocol readiness smoke — next-work prompt P0 (no customer NDA data)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.tools.evaluate_detection_precision import _validate_adjudication_protocol

REPO = Path(__file__).resolve().parents[2]
PRECISION_DIR = REPO / "samples" / "benchmarks" / "detection-precision"


class NextWorkProtocolHarnessTests(unittest.TestCase):
    def test_customer_template_method_is_publishable_when_adjudicated(self) -> None:
        template = json.loads(
            (PRECISION_DIR / "labels-customer-protocol-template.json").read_text(encoding="utf-8")
        )
        # Draft template must not look publishable as-is
        ok_draft, count = _validate_adjudication_protocol(
            template,
            dataset_status=str(template["dataset_status"]),
            scope_reference=str(template.get("scope_reference")),
            unresolved_count=0,
        )
        self.assertFalse(ok_draft)
        self.assertGreaterEqual(count, 2)

        # Same shape with adjudicated status + real-looking scope + timezone completed_at
        payload = dict(template)
        adjudication = dict(template["adjudication"])
        adjudication["completed_at"] = "2026-07-17T12:00:00+03:00"
        payload["adjudication"] = adjudication
        ok, _ = _validate_adjudication_protocol(
            payload,
            dataset_status="adjudicated",
            scope_reference="SIGNED-SCOPE-MEMO-REF",
            unresolved_count=0,
        )
        self.assertTrue(
            ok,
            "dual_independent in customer template must be accepted by publishable gate",
        )

    def test_draft_customer_template_never_implies_product_claim(self) -> None:
        template = json.loads(
            (PRECISION_DIR / "labels-customer-protocol-template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(template["dataset_status"], "draft")
        agreement = json.loads(
            (PRECISION_DIR / "agreement-template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(agreement["artifact_type"], "adjudicator_agreement")
        self.assertIn("TEMPLATE ONLY", " ".join(agreement.get("notes", [])))

    def test_agreement_template_passes_kappa_alpha_shape(self) -> None:
        agreement = json.loads(
            (PRECISION_DIR / "agreement-template.json").read_text(encoding="utf-8")
        )
        self.assertTrue(agreement["pass_threshold_0_60"])
        self.assertTrue(agreement["pass_alpha_0_67"])
        self.assertGreaterEqual(agreement["adjudicator_count"], 2)


if __name__ == "__main__":
    unittest.main()
