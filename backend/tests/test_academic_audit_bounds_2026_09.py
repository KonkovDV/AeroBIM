"""Bounded inputs from the 2026-09-05 academic static audit (M-04 / L-07)."""

from __future__ import annotations

import unittest
from pathlib import Path

from pydantic import ValidationError

from aerobim.presentation.http.csrf import BFF_CSRF_HEADER, BFF_CSRF_VALUE
from aerobim.presentation.http.schemas import (
    AnalyzeProjectPackageRequest,
    NormRuleHitlEventRequest,
)


class RuleDiffBoundTests(unittest.TestCase):
    def test_small_rule_diff_accepted(self) -> None:
        payload = NormRuleHitlEventRequest(
            event_type="norm_rule_proposed",
            base_pack_path="packs/demo.json",
            rule_diff={"rule_id": "SAM-AR-001", "evidence_text": "a"},
        )
        self.assertEqual(payload.rule_diff["rule_id"], "SAM-AR-001")

    def test_rule_diff_rejects_too_many_keys(self) -> None:
        with self.assertRaises(ValidationError):
            NormRuleHitlEventRequest(
                event_type="norm_rule_proposed",
                base_pack_path="packs/demo.json",
                rule_diff={f"k{i}": "x" for i in range(65)},
            )

    def test_rule_diff_rejects_oversized_json(self) -> None:
        with self.assertRaises(ValidationError):
            NormRuleHitlEventRequest(
                event_type="norm_rule_proposed",
                base_pack_path="packs/demo.json",
                rule_diff={"rule_id": "SAM-AR-001", "blob": "x" * 40_000},
            )


class AnalyzePathBoundTests(unittest.TestCase):
    def test_norm_rule_pack_path_items_are_length_capped(self) -> None:
        with self.assertRaises(ValidationError):
            AnalyzeProjectPackageRequest(norm_rule_pack_paths=["a" * 2049])


class CsrfHeaderContractTests(unittest.TestCase):
    def test_frontend_csrf_constants_match_backend(self) -> None:
        front = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "csrf.ts"
        text = front.read_text(encoding="utf-8")
        self.assertIn(BFF_CSRF_HEADER, text)
        self.assertIn(BFF_CSRF_VALUE, text)
        api = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "api.ts"
        self.assertIn("aerobimCsrfHeaders", api.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
