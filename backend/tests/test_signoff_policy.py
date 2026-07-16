"""Unit tests for sign-off capability gating."""

from __future__ import annotations

import unittest

from aerobim.application.services.signoff_policy import (
    failed_capabilities_blocking_pass,
    summary_passed_after_capabilities,
)
from aerobim.domain.models import CapabilityState, CapabilityStatus, ReportCapabilities


class SignoffPolicyTests(unittest.TestCase):
    def test_failed_norm_pack_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            norm_rule_packs=CapabilityStatus(CapabilityState.FAILED, "missing pack"),
        )
        self.assertEqual(failed_capabilities_blocking_pass(caps), ("norm_rule_packs",))
        self.assertFalse(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_skipped_clash_does_not_block_pass(self) -> None:
        caps = ReportCapabilities(
            clash=CapabilityStatus(CapabilityState.SKIPPED, "ifcclash missing"),
        )
        self.assertEqual(failed_capabilities_blocking_pass(caps), ())
        self.assertTrue(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_errors_block_pass_even_when_capabilities_ok(self) -> None:
        caps = ReportCapabilities()
        self.assertFalse(summary_passed_after_capabilities(error_count=1, capabilities=caps))

    def test_failed_calculation_match_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            calculation_match=CapabilityStatus(CapabilityState.FAILED, "load mismatch"),
        )
        self.assertEqual(failed_capabilities_blocking_pass(caps), ("calculation_match",))
        self.assertFalse(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_failed_dwg_dxf_blocks_pass(self) -> None:
        caps = ReportCapabilities(
            dwg_dxf=CapabilityStatus(CapabilityState.FAILED, "native DWG missing ODA"),
        )
        self.assertEqual(failed_capabilities_blocking_pass(caps), ("dwg_dxf",))
        self.assertFalse(summary_passed_after_capabilities(error_count=0, capabilities=caps))

    def test_not_verified_dwg_dxf_does_not_block_pass(self) -> None:
        caps = ReportCapabilities(
            dwg_dxf=CapabilityStatus(CapabilityState.NOT_VERIFIED, "DXF only"),
        )
        self.assertEqual(failed_capabilities_blocking_pass(caps), ())
        self.assertTrue(summary_passed_after_capabilities(error_count=0, capabilities=caps))


if __name__ == "__main__":
    unittest.main()
