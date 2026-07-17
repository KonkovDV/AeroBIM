from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
RULE_PACKS_DIR = REPO_ROOT / "samples" / "rule-packs"
SCHEMA = RULE_PACKS_DIR / "norm-rule-pack.schema.json"


def _pack_files() -> list[Path]:
    return sorted(p for p in RULE_PACKS_DIR.glob("*.json") if p.name != SCHEMA.name)


class NormRulePackSchemaTests(unittest.TestCase):
    """CI gate: every shipped rule pack validates against the published schema."""

    def test_rule_pack_dir_has_at_least_one_pack(self) -> None:
        self.assertTrue(_pack_files(), "expected at least one sample rule pack")

    def test_all_rule_packs_conform_to_schema(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for pack in _pack_files():
            with self.subTest(pack=pack.name):
                payload = json.loads(pack.read_text(encoding="utf-8"))
                errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
                self.assertEqual(errors, [], f"{pack.name}: {[e.message for e in errors]}")

    def test_all_rule_packs_load_via_loader(self) -> None:
        """Schema validity and loader acceptance must agree (no drift)."""
        loader = JsonNormRulePackLoader()
        for pack in _pack_files():
            with self.subTest(pack=pack.name):
                loaded = loader.load(pack)
                self.assertTrue(loaded.rules, f"{pack.name}: expected non-empty rules")
                self.assertEqual(len(loaded.sha256), 64)

    def test_approved_status_requires_approval_block_in_schema(self) -> None:
        """Guard the approval invariant the loader also enforces."""
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        base = json.loads(
            (RULE_PACKS_DIR / "residential-ar-reference-template.json").read_text(encoding="utf-8")
        )
        base["status"] = "approved"
        base.pop("approval", None)
        base.pop("approval_ref", None)
        errors = list(validator.iter_errors(base))
        self.assertTrue(errors, "approved pack without approval block must fail schema")

    def test_customer_approved_requires_full_approval_block_in_schema(self) -> None:
        """Schema must match loader: ref-only is not enough for customer_approved."""
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        base = json.loads(
            (RULE_PACKS_DIR / "customer-norm-pack-intake-template.json").read_text(
                encoding="utf-8"
            )
        )
        base["status"] = "customer_approved"
        base["approval"] = None
        base["approval_ref"] = None
        errors = list(validator.iter_errors(base))
        self.assertTrue(
            errors, "customer_approved without approval block must fail schema"
        )
        # approval_ref alone must still fail (closes RT-002 schema bypass)
        base["approval_ref"] = "SIGNED-MEMO-REF"
        errors_ref_only = list(validator.iter_errors(base))
        self.assertTrue(
            errors_ref_only,
            "customer_approved with approval_ref only must fail schema",
        )
        base["approval"] = {
            "approved_by": "customer-qa",
            "approved_at": "2026-07-17T12:00:00+03:00",
            "scope_reference": "SIGNED-MEMO-REF",
        }
        errors_ok = list(validator.iter_errors(base))
        self.assertEqual(errors_ok, [], [e.message for e in errors_ok])


if __name__ == "__main__":
    unittest.main()
