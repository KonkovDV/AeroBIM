"""samolet_pilot_demo: clash/MEP out of scope, not faked; LLM still closed.

Does not close RT-003. Does not weaken samolet_pilot / production.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from aerobim.application.services.capability_policy import (
    apply_demo_scope_honesty,
    build_signoff_policy,
    is_closed_egress_profile,
    is_customer_hard_profile,
    normalize_signoff_profile,
)
from aerobim.core.config.settings import Settings
from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities


class SamoletPilotDemoProfileTests(unittest.TestCase):
    def test_alias_and_classification(self) -> None:
        self.assertEqual(normalize_signoff_profile("pilot_demo"), "samolet_pilot_demo")
        self.assertFalse(is_customer_hard_profile("samolet_pilot_demo"))
        self.assertTrue(is_customer_hard_profile("samolet_pilot"))
        self.assertTrue(is_closed_egress_profile("samolet_pilot_demo"))

    def test_demo_does_not_require_clash_or_mep(self) -> None:
        policy = build_signoff_policy(profile="samolet_pilot_demo")
        self.assertFalse(policy.require_clash)
        self.assertFalse(policy.require_mep_system_clash)
        self.assertFalse(policy.clash_affects_pass)
        self.assertFalse(policy.require_bsi_schema)
        self.assertTrue(policy.enforce_object_acl)
        self.assertTrue(policy.audit_fail_closed)
        self.assertTrue(policy.summary_passed(error_count=0, capabilities=ReportCapabilities()))

    def test_demo_ignores_require_clash_true_override(self) -> None:
        policy = build_signoff_policy(profile="samolet_pilot_demo", require_clash=True)
        self.assertFalse(policy.require_clash)

    def test_customer_pilot_still_requires_clash(self) -> None:
        policy = build_signoff_policy(profile="samolet_pilot")
        self.assertTrue(policy.require_clash)
        self.assertTrue(policy.require_mep_system_clash)
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=ReportCapabilities()))

    def test_honesty_stamp_rewrites_unverified_not_ok(self) -> None:
        stamped = apply_demo_scope_honesty(ReportCapabilities())
        self.assertIs(stamped.clash.status, CapabilityState.SKIPPED)
        self.assertIn("RT-003 OPEN", stamped.clash.reason or "")
        self.assertIs(stamped.mep_system_clash.status, CapabilityState.SKIPPED)
        self.assertIn("not faked", stamped.mep_system_clash.reason or "")

    def test_honesty_stamp_keeps_failed_engine_result(self) -> None:
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.FAILED, "ifcclash crashed"),
        )
        stamped = apply_demo_scope_honesty(caps)
        self.assertIs(stamped.clash.status, CapabilityState.FAILED)

    def test_failed_extraction_integrity_still_blocks_demo(self) -> None:
        caps = ReportCapabilities(
            extraction_integrity=CapabilityStatus(
                CapabilityState.FAILED, "render vs extract mismatch"
            )
        )
        policy = build_signoff_policy(profile="samolet_pilot_demo")
        self.assertFalse(policy.summary_passed(error_count=0, capabilities=caps))

    def test_settings_demo_from_env(self) -> None:
        env = {
            "AEROBIM_ENV": "development",
            "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot_demo",
            "AEROBIM_REQUIRE_CLASH": "true",
            "AEROBIM_REQUIRE_MEP_SYSTEM_CLASH": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            settings = Settings.from_env()
        self.assertEqual(settings.signoff_profile, "samolet_pilot_demo")
        self.assertFalse(settings.require_clash)
        self.assertFalse(settings.require_mep_system_clash)
        self.assertFalse(settings.require_bsi_schema)
        self.assertTrue(settings.enforce_object_acl)
        self.assertFalse(settings.llm_local_ready())
        self.assertFalse(settings.vlm_advisory_ready())

    def test_demo_forbidden_outside_dev_env(self) -> None:
        env = {
            "AEROBIM_ENV": "production",
            "AEROBIM_SIGNOFF_PROFILE": "samolet_pilot_demo",
            "AEROBIM_API_BEARER_TOKEN": "x" * 32,
        }
        with patch.dict(os.environ, env, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                Settings.from_env()
        self.assertIn("samolet_pilot_demo", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
