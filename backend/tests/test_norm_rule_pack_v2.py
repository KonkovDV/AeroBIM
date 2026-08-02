"""WP-04: norm pack v2 structure, expert confirmation gate, approval fail-closed."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.domain.models import RulePackStatus
from aerobim.domain.norm_pack_hash import compute_norm_pack_content_hash
from aerobim.domain.norm_rule_eligibility import (
    can_contribute_positive_norm_outcome,
    expert_required_report,
    has_expert_confirmation,
    is_rule_checkable,
    list_awaiting_expert_confirmation,
    list_expert_required_rules,
    partition_checkable_rules,
)
from aerobim.infrastructure.adapters.json_norm_rule_pack_loader import JsonNormRulePackLoader

REPO_ROOT = Path(__file__).resolve().parents[2]
V2_PACK = REPO_ROOT / "samples" / "rule-packs" / "norm-pack-v2-draft-example.json"
INTAKE_PACK = REPO_ROOT / "samples" / "rule-packs" / "customer-norm-pack-intake-template.json"
SCHEMA = REPO_ROOT / "samples" / "rule-packs" / "norm-rule-pack.schema.json"
RULE_IDS = (
    "V2-AR-SPACE-EXTERNAL-001",
    "V2-AR-FIRE-RATING-EXPERT-001",
    "V2-AR-AWAITING-CONFIRM-001",
)


def _approved_v2_payload() -> dict:
    payload = json.loads(V2_PACK.read_text(encoding="utf-8"))
    payload["status"] = "customer_approved"
    payload["claim_labels"] = ["customer-evidence"]
    payload["jurisdiction"] = "RF"
    payload["customer_approval_ref"] = "SIGNED-MEMO-REF"
    payload["approval_ref"] = "SIGNED-MEMO-REF"
    payload["approval"] = {
        "approved_by": "customer-qa",
        "approval_date": "2026-08-02T12:00:00+03:00",
        "approval_status": "customer_approved",
        "document_title": "Fixture approved v2 pack (does not close RT-002)",
        "document_edition": "2026-08",
        "effective_date": "2026-08-01",
        "scope_reference": "SIGNED-MEMO-REF",
    }
    payload["pack_hash"] = compute_norm_pack_content_hash(payload)
    return payload


class NormPackV2SchemaTests(unittest.TestCase):
    def test_v2_example_and_intake_conform_to_schema(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for pack in (V2_PACK, INTAKE_PACK):
            with self.subTest(pack=pack.name):
                payload = json.loads(pack.read_text(encoding="utf-8"))
                errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
                self.assertEqual(errors, [], [e.message for e in errors])

    def test_customer_approved_without_approval_fails_schema(self) -> None:
        import jsonschema

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        base = _approved_v2_payload()
        base["approval"] = None
        base["approval_ref"] = "REF-ONLY"
        base["customer_approval_ref"] = "REF-ONLY"
        errors = list(validator.iter_errors(base))
        self.assertTrue(errors, "customer_approved with ref-only must fail schema")


class NormPackV2LoaderAndGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loader = JsonNormRulePackLoader()

    def test_loads_v2_draft_example_with_all_rules(self) -> None:
        pack = self.loader.load(V2_PACK)
        self.assertEqual(pack.schema_version, "2.0.0")
        self.assertEqual(pack.status, RulePackStatus.DRAFT)
        self.assertTrue(pack.advisory_only)
        self.assertEqual(pack.norm_edition, "SP-54.13330-draft")
        self.assertEqual(pack.norm_edition_date, "2026-08-01")
        self.assertEqual(len(pack.rules), 3)
        by_id = {rule.rule_id: rule for rule in pack.rules}
        for rule_id in RULE_IDS:
            self.assertIn(rule_id, by_id)

    def test_each_included_rule_regression(self) -> None:
        pack = self.loader.load(V2_PACK)
        by_id = {rule.rule_id: rule for rule in pack.rules}

        confirmed = by_id["V2-AR-SPACE-EXTERNAL-001"]
        self.assertEqual(confirmed.execution_mode, "deterministic")
        self.assertTrue(has_expert_confirmation(confirmed))
        self.assertTrue(is_rule_checkable(confirmed, pack=pack))
        self.assertEqual(confirmed.norm_clause, "7.1.2")
        self.assertIsNotNone(confirmed.rase)
        self.assertEqual(confirmed.rase.exclusion, "Technical shafts marked out of scope in scope memo")

        expert = by_id["V2-AR-FIRE-RATING-EXPERT-001"]
        self.assertEqual(expert.execution_mode, "expert_required")
        self.assertFalse(is_rule_checkable(expert, pack=pack))
        self.assertIn(expert, list_expert_required_rules(pack))

        awaiting = by_id["V2-AR-AWAITING-CONFIRM-001"]
        self.assertEqual(awaiting.execution_mode, "deterministic")
        self.assertFalse(has_expert_confirmation(awaiting))
        self.assertFalse(is_rule_checkable(awaiting, pack=pack))
        self.assertIn(awaiting, list_awaiting_expert_confirmation(pack))

        checkable, deferred = partition_checkable_rules(pack)
        self.assertEqual([r.rule_id for r in checkable], ["V2-AR-SPACE-EXTERNAL-001"])
        self.assertEqual(len(deferred), 2)

    def test_llm_draft_without_journal_does_not_enter_checking(self) -> None:
        pack = self.loader.load(V2_PACK)
        awaiting = next(r for r in pack.rules if r.rule_id == "V2-AR-AWAITING-CONFIRM-001")
        self.assertFalse(is_rule_checkable(awaiting, pack=pack))
        self.assertFalse(can_contribute_positive_norm_outcome(pack, awaiting))

    def test_customer_approved_without_approval_ref_fails_closed(self) -> None:
        payload = _approved_v2_payload()
        payload["approval"] = None
        payload["approval_ref"] = None
        payload["customer_approval_ref"] = None
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "no-approval.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "require an approval object"):
                self.loader.load(path)

    def test_customer_approved_ref_only_fails_closed(self) -> None:
        payload = _approved_v2_payload()
        payload["approval"] = None
        payload["approval_ref"] = "SIGNED-MEMO-REF"
        payload["customer_approval_ref"] = "SIGNED-MEMO-REF"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "ref-only.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approval_ref alone is not sufficient"):
                self.loader.load(path)

    def test_full_customer_approved_v2_loads_but_does_not_claim_rt002_closed(self) -> None:
        payload = _approved_v2_payload()
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "approved-v2.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            pack = self.loader.load(path)
        self.assertEqual(pack.status, RulePackStatus.APPROVED)
        self.assertFalse(pack.advisory_only)
        self.assertIsNotNone(pack.customer_approval_ref)
        # Engineering fixture can load as approved; RT-002 stays a customer evidence gate.
        self.assertTrue(can_contribute_positive_norm_outcome(pack))
        confirmed = next(r for r in pack.rules if r.rule_id == "V2-AR-SPACE-EXTERNAL-001")
        self.assertTrue(can_contribute_positive_norm_outcome(pack, confirmed))
        expert = next(r for r in pack.rules if r.rule_id == "V2-AR-FIRE-RATING-EXPERT-001")
        self.assertFalse(can_contribute_positive_norm_outcome(pack, expert))

    def test_expired_and_expert_required_statuses_are_advisory(self) -> None:
        for status in ("expired", "inapplicable", "expert_required"):
            with self.subTest(status=status):
                payload = json.loads(V2_PACK.read_text(encoding="utf-8"))
                payload["status"] = status
                with tempfile.TemporaryDirectory() as temporary_directory:
                    path = Path(temporary_directory) / f"{status}.json"
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    pack = self.loader.load(path)
                self.assertTrue(pack.advisory_only)
                self.assertFalse(can_contribute_positive_norm_outcome(pack))

    def test_expert_required_report_lists_non_auto_rules(self) -> None:
        pack = self.loader.load(V2_PACK)
        report = expert_required_report(pack)
        self.assertEqual(report["expert_required_count"], 1)
        self.assertEqual(report["expert_required"][0]["rule_id"], "V2-AR-FIRE-RATING-EXPERT-001")
        self.assertEqual(report["awaiting_confirmation_count"], 1)
        self.assertIn("RT-002", report["claim_boundary"])

    def test_v2_missing_journal_key_rejected(self) -> None:
        payload = json.loads(V2_PACK.read_text(encoding="utf-8"))
        del payload["rules"][0]["expert_confirmation_journal"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "no-journal.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "expert_confirmation_journal"):
                self.loader.load(path)


class NormPackV2CliToolTests(unittest.TestCase):
    def test_list_expert_required_tool(self) -> None:
        from aerobim.tools.list_expert_required_norm_rules import main

        with tempfile.TemporaryDirectory() as temporary_directory:
            out = Path(temporary_directory) / "expert.json"
            code = main(["--pack", str(V2_PACK), "--output", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["expert_required_count"], 1)


if __name__ == "__main__":
    unittest.main()
