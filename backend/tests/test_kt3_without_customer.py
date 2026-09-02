"""KT#3 without Samolet files stays re-scope and NO_GO."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aerobim.domain.kt3_without_customer import (
    CLAIM_LEVEL,
    OWNER_DECISION_DATE,
    PLAN_B_DECISION,
    PROGRAM_FORK_DATE,
    Kt3WithoutCustomerError,
    assemble_kt3_without_customer,
    render_markdown,
    require_honest_kt3_payload,
)
from aerobim.tools.run_kt3_without_customer import build_payload
from aerobim.tools.run_kt3_without_customer import main as kt3_main

REPO_ROOT = Path(__file__).resolve().parents[2]


class Kt3WithoutCustomerTests(unittest.TestCase):
    def test_live_repo_assembles_re_scope_and_keeps_blockers_open(self) -> None:
        payload = assemble_kt3_without_customer(
            REPO_ROOT, generated_at=f"{OWNER_DECISION_DATE}T00:00:00+00:00"
        )
        self.assertEqual(payload["plan_b_decision"], PLAN_B_DECISION)
        self.assertEqual(payload["owner_decision_date"], OWNER_DECISION_DATE)
        self.assertEqual(payload["program_fork_date"], PROGRAM_FORK_DATE)
        self.assertEqual(payload["checkpoint"], "NO_GO")
        self.assertEqual(payload["claim_level"], CLAIM_LEVEL)
        self.assertFalse(payload["customer_files_expected"])
        self.assertFalse(payload["waiting_for_customer"])
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["closes_rt002"])
        self.assertFalse(payload["closes_rt003"])
        self.assertFalse(payload["nda_corpus_in_git"])
        self.assertEqual(payload["schema_version"], "1.2.0")
        self.assertEqual(payload["rt002_split"]["b_corporate"], "OPEN")
        self.assertTrue(payload["rt002_split"]["undifferentiated_closed_forbidden"])
        self.assertTrue(any("90%" in item for item in payload["tz_explicit_gaps"]))
        roles = {row["role"] for row in payload["evidence"]}
        self.assertIn("tz_v2", roles)
        self.assertIn("kt3_jury_card", roles)
        self.assertIn("moscow_agr_ruler", roles)
        self.assertIn("kt3_operator_runbook", roles)
        self.assertIn("kt3_tracker_card", roles)
        self.assertIn("tz_v1_brief", roles)
        self.assertIn("typical_errors_catalog", roles)
        self.assertEqual(len(payload["paper_objects"]), 4)
        self.assertEqual(payload["typical_errors"]["customer_confirmed_patterns"], 0)
        self.assertGreaterEqual(payload["typical_errors"]["pattern_count"], 20)
        self.assertEqual(payload["tracker"]["item_count"], 6)
        self.assertEqual(payload["tracker_eight"]["item_count"], 8)
        self.assertEqual(payload["tracker_eight"]["auth_bff_status"], "NOT_IMPLEMENTED")
        self.assertIn("kt3_tracker_eight", {row["role"] for row in payload["evidence"]})
        self.assertEqual(payload["mik_m2_m8"], "VERIFY_WITH_OPERATOR")
        self.assertIn("run_kt3_jury", payload["jury_command"])
        self.assertEqual(payload["intake_true_gates"], [])
        self.assertFalse(payload["validation_effectiveness_started"])
        self.assertTrue(all(row["present"] for row in payload["evidence"]))

    def test_payload_rejects_closed_blockers_and_customer_expectation(self) -> None:
        base = assemble_kt3_without_customer(
            REPO_ROOT, generated_at=f"{OWNER_DECISION_DATE}T00:00:00+00:00"
        )
        dirty = dict(base)
        dirty["closes_rt001"] = True
        with self.assertRaises(Kt3WithoutCustomerError):
            require_honest_kt3_payload(dirty)
        dirty = dict(base)
        dirty["customer_files_expected"] = True
        with self.assertRaises(Kt3WithoutCustomerError):
            require_honest_kt3_payload(dirty)
        dirty = dict(base)
        dirty["waiting_for_customer"] = True
        with self.assertRaises(Kt3WithoutCustomerError):
            require_honest_kt3_payload(dirty)
        dirty = dict(base)
        dirty["checkpoint"] = "GO"
        with self.assertRaises(Kt3WithoutCustomerError):
            require_honest_kt3_payload(dirty)
        dirty = dict(base)
        dirty["nda_corpus_in_git"] = True
        with self.assertRaises(Kt3WithoutCustomerError):
            require_honest_kt3_payload(dirty)

    def test_cli_writes_artifacts_and_prints_re_scope(self) -> None:
        code = kt3_main(["--generated-at", f"{OWNER_DECISION_DATE}T00:00:00+00:00"])
        self.assertEqual(code, 0)
        latest = REPO_ROOT / "artifacts" / "kt3-without-customer" / "latest.json"
        self.assertTrue(latest.is_file())
        payload = json.loads(latest.read_text(encoding="utf-8"))
        self.assertEqual(payload["plan_b_decision"], "re-scope")
        self.assertFalse(payload["closes_rt001"])
        self.assertFalse(payload["nda_corpus_in_git"])

    def test_build_payload_wrapper_matches_domain(self) -> None:
        payload = build_payload(REPO_ROOT, generated_at=f"{OWNER_DECISION_DATE}T00:00:00+00:00")
        self.assertEqual(payload["artifact_type"], "kt3_without_customer")
        self.assertIn("run_demo_ifc_acceptance_gate", payload["demo_command"])

    def test_markdown_uses_json_false_not_python_repr(self) -> None:
        payload = assemble_kt3_without_customer(
            REPO_ROOT, generated_at=f"{OWNER_DECISION_DATE}T00:00:00+00:00"
        )
        md = render_markdown(payload)
        self.assertIn("- closes_rt001: **false**", md)
        self.assertIn("- closes_rt002: **false**", md)
        self.assertIn("- closes_rt003: **false**", md)
        self.assertNotIn("**False**", md)
        self.assertIn("customer_files_expected: false", md)
        self.assertIn("nda_corpus_in_git: false", md)
        self.assertIn("KT3_JURY_FAQ_2026_08_25.md", md)
        self.assertIn("KT3_TRACKER_SIX_TASKS_2026_08.md", md)

    def test_jury_card_and_runbook_keep_honesty_pins(self) -> None:
        faq = (REPO_ROOT / "docs" / "demo" / "KT3_JURY_FAQ_2026_08_25.md").read_text(
            encoding="utf-8"
        )
        runbook = (REPO_ROOT / "docs" / "demo" / "KT3_OPERATOR_RUNBOOK_2026_08_25.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("NO_GO", faq)
        self.assertIn("run_demo_ifc_acceptance_gate", faq)
        self.assertIn("RT-002 CLOSED", faq)
        self.assertIn("run_demo_ifc_acceptance_gate", runbook)
        self.assertIn("run_kt3_jury", runbook)
        self.assertIn("IDS-Wall Fire Rating", runbook)
        self.assertIn("nda_corpus_in_git=false", runbook)
        self.assertIn("samolet_pilot", runbook)
        self.assertIn("лучше Iversen", faq)
        self.assertIn("Iversen", faq)
        self.assertIn("Fuchs", faq)
        self.assertIn("approval_ref", faq)
