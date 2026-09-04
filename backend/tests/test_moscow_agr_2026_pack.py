"""City-published moscow_agr_2026 pack loads; does not close RT-002b."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.models import RulePackStatus
from aerobim.domain.norm_pack_hash import compute_norm_pack_content_hash
from aerobim.domain.norm_rule_eligibility import (
    is_rule_checkable,
    list_awaiting_expert_confirmation,
)
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_PATH = REPO_ROOT / "samples" / "norm-packs" / "moscow_agr_2026" / "pack.json"
SCHEMA = REPO_ROOT / "samples" / "rule-packs" / "norm-rule-pack.schema.json"


class MoscowAgr2026PackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonNormRulePackLoader()

    def test_pack_file_exists(self) -> None:
        self.assertTrue(PACK_PATH.is_file(), PACK_PATH)

    def test_schema_accepts_city_approved_pack(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
        errors = sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(payload),
            key=lambda err: list(err.path),
        )
        self.assertEqual(errors, [], [err.message for err in errors])

    def test_declared_hash_matches_canonical_content(self) -> None:
        payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
        declared = payload.get("pack_hash")
        self.assertIsInstance(declared, str)
        self.assertEqual(len(declared), 64)
        self.assertEqual(compute_norm_pack_content_hash(payload), declared.lower())

    def test_loader_accepts_city_publisher_approval(self) -> None:
        pack = self.loader.load(PACK_PATH)
        self.assertEqual(pack.pack_id, "MOSCOW-AGR-2026")
        self.assertEqual(pack.status, RulePackStatus.APPROVED)
        self.assertFalse(pack.advisory_only)
        self.assertEqual(pack.jurisdiction, "г. Москва")
        self.assertTrue(pack.pack_hash)
        self.assertTrue(pack.approval_reference)
        self.assertNotIn("synthetic", pack.claim_labels)
        self.assertNotIn("fixture", pack.claim_labels)
        self.assertEqual(len(pack.rules), 6)
        self.assertTrue(all(rule.property_set.startswith("RusSet_") for rule in pack.rules))

    def test_v2_empty_journal_does_not_enter_checking(self) -> None:
        pack = self.loader.load(PACK_PATH)
        awaiting = list_awaiting_expert_confirmation(pack)
        self.assertEqual(len(awaiting), len(pack.rules))
        for rule in pack.rules:
            self.assertFalse(is_rule_checkable(rule, pack=pack), rule.rule_id)

    def test_does_not_claim_samolet_customer_profile(self) -> None:
        boundary = (PACK_PATH.parent / "APPROVAL_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("RT-002b", boundary)
        self.assertIn("customer_go", boundary)
        self.assertIn("Samolet internals remain out of scope", boundary)


if __name__ == "__main__":
    unittest.main()
