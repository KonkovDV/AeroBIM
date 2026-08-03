"""RT-W-02 — honesty surface keys must not drift without failing CI."""

from __future__ import annotations

import unittest

from aerobim.domain.system_capabilities import build_system_capabilities_payload


class HonestySurfaceContractTests(unittest.TestCase):
    """Lock claim text that jury/customer see on /v1/system/capabilities."""

    def test_llm_advisory_honesty_keys_locked(self) -> None:
        payload = build_system_capabilities_payload()
        advisory = payload["llm_advisory"]
        self.assertIsInstance(advisory, dict)

        self.assertEqual(advisory["token_budget_scope"], "process_local_or_file_shared")
        self.assertIn("AEROBIM_LLM_BUDGET_LEDGER", advisory["token_budget_note"])
        self.assertIn("RT-BUDGET-03", advisory["token_budget_note"])
        self.assertIn("lock_degraded=true", advisory["token_budget_note"])

        pii = advisory["pii_gate"]
        self.assertTrue(pii["active"])
        self.assertEqual(pii["effectiveness_on_customer_sheets"], "NOT_MEASURED")
        self.assertIn("not measured", pii["claim_boundary"].lower())
        self.assertEqual(
            set(pii["exclusion_counters"]),
            {"excluded_by_role", "excluded_by_geometry", "excluded_unknown_role"},
        )

        egress = advisory["content_marking_egress"]
        self.assertEqual(
            egress["http_remark_field"],
            "remark.ai_generated + remark.content_marking",
        )
        self.assertEqual(
            egress["bcf_description_provenance"],
            "ai_generated=true;expert_confirmation_required=true",
        )
        self.assertEqual(egress["bcf_label"], "ai_generated:true")

        # Guardrail: these seven keys must remain present (rename = fail the build).
        for key in (
            "token_budget_scope",
            "token_budget_note",
            "pii_gate",
            "http_remark_field",
            "bcf_description_provenance",
            "bcf_label",
            "effectiveness_on_customer_sheets",
        ):
            if key in {"http_remark_field", "bcf_description_provenance", "bcf_label"}:
                self.assertIn(key, egress)
            elif key == "effectiveness_on_customer_sheets":
                self.assertIn(key, pii)
            else:
                self.assertIn(key, advisory)

    def test_pii_effectiveness_cannot_silently_become_measured(self) -> None:
        payload = build_system_capabilities_payload()
        value = payload["llm_advisory"]["pii_gate"]["effectiveness_on_customer_sheets"]
        self.assertEqual(value, "NOT_MEASURED")
        self.assertNotIn(value.upper(), {"MEASURED", "VERIFIED", "OK", "PASS"})


if __name__ == "__main__":
    unittest.main()
