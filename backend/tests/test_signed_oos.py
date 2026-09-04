
"""Signed OOS templates do not license skip until signer+statement lock."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.checkpoint import CHECKPOINT
from aerobim.domain.signed_oos import (
    ALLOWED_STATEMENTS,
    OOS_KINDS,
    evaluate_oos,
    oos_snapshot,
    unsigned_template,
)

_REPO = Path(__file__).resolve().parents[2]
_SAMPLES = _REPO / "samples" / "oos"


class SignedOosTests(unittest.TestCase):
    def test_unsigned_template_does_not_license_skip(self) -> None:
        for kind in OOS_KINDS:
            decision = evaluate_oos(unsigned_template(kind))
            self.assertFalse(decision.accepted)
            self.assertFalse(decision.licenses_unmeasured_speech)
            self.assertEqual(decision.status, "unsigned")
            self.assertFalse(decision.closes_rt001)
            self.assertFalse(decision.closes_rt003)

    def test_wrong_statement_is_rejected(self) -> None:
        payload = unsigned_template("qto_space_area")
        payload["signer"] = "Appointing party"
        payload["signed_at"] = "2026-08-27"
        payload["scope_memo"] = "task 3 area"
        payload["statement"] = "Areas were checked against TEP"
        decision = evaluate_oos(payload)
        self.assertEqual(decision.status, "rejected")
        self.assertFalse(decision.licenses_unmeasured_speech)

    def test_rt_closed_flag_is_rejected(self) -> None:
        payload = unsigned_template("mep_federated")
        payload["signer"] = "Appointing party"
        payload["signed_at"] = "2026-08-27"
        payload["scope_memo"] = "no IOS IFC"
        payload["closes_rt003"] = True
        decision = evaluate_oos(payload)
        self.assertEqual(decision.status, "rejected")

    def test_signed_matching_statement_licenses_unmeasured_speech_only(self) -> None:
        payload = unsigned_template("rebar_class4")
        payload["signer"] = "Appointing party"
        payload["signed_at"] = "2026-08-27T00:00:00+00:00"
        payload["scope_memo"] = "task 7 class 4"
        decision = evaluate_oos(payload)
        self.assertTrue(decision.accepted)
        self.assertTrue(decision.licenses_unmeasured_speech)
        self.assertEqual(decision.status, "accepted_unmeasured")
        self.assertFalse(decision.closes_rt001)
        self.assertFalse(decision.closes_rt003)
        self.assertEqual(payload["statement"], ALLOWED_STATEMENTS["rebar_class4"])

    def test_snapshot_has_no_accepted_oos(self) -> None:
        snap = oos_snapshot()
        self.assertEqual(snap["checkpoint"], CHECKPOINT)
        self.assertFalse(snap["any_accepted"])
        self.assertTrue(snap["templates_unsigned"])
        self.assertEqual(snap["detected_count"], 0)

    def test_sample_templates_on_disk_are_unsigned(self) -> None:
        for kind in OOS_KINDS:
            path = _SAMPLES / f"{kind}.unsigned.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(evaluate_oos(payload).status, "unsigned")


if __name__ == "__main__":
    unittest.main()
