"""HybridRouteGate must block VLM smoke before any client call (RT-WP02-03)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.tools.vlm_advisory_smoke import run_smoke
from aerobim.tools.vlm_smoke_gate import (
    evaluate_vlm_smoke_egress,
    gate_blocks_external,
    smoke_signoff_blocks_external,
)


class VlmSmokeGateTests(unittest.TestCase):
    def test_empty_tenant_blocks_external(self) -> None:
        result = evaluate_vlm_smoke_egress(
            tenant_id="",
            sheet_id="S1",
            image_name="a.png",
        )
        self.assertTrue(gate_blocks_external(result))
        self.assertEqual(result.egress_bytes_estimate, 0)

    def test_open_data_public_with_guard_allows_external(self) -> None:
        result = evaluate_vlm_smoke_egress(
            tenant_id="open-data-smoke",
            sheet_id="S1",
            image_name="fixture.png",
        )
        self.assertFalse(gate_blocks_external(result))
        self.assertTrue(result.may_call_external)
        self.assertGreater(result.egress_bytes_estimate, 0)

    def test_maskless_gate_blocks_public_payload(self) -> None:
        result = evaluate_vlm_smoke_egress(
            tenant_id="open-data-smoke",
            sheet_id="S1",
            image_name="fixture.png",
            gate=HybridRouteGate(),  # no PrivacyGuard
        )
        self.assertTrue(gate_blocks_external(result))

    def test_whole_sheet_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "open.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
            with patch.dict(
                "os.environ",
                {
                    "AEROBIM_VLM_API_BASE_URL": "https://example.invalid",
                    "AEROBIM_VLM_API_KEY": "test-key",
                },
            ):
                report = run_smoke(image, sheet_id="S1", tenant_id="open-data-smoke")
        self.assertEqual(report["status"], "NOT_RUN")
        self.assertIn("whole-sheet", str(report["reason"]))

    def test_pilot_signoff_blocks_smoke(self) -> None:
        class _Pilot:
            signoff_profile = "samolet_pilot"

        reason = smoke_signoff_blocks_external(settings=_Pilot())
        self.assertIsNotNone(reason)
        self.assertIn("samolet_pilot", reason or "")

    def test_advisory_smoke_blocked_never_builds_client(self) -> None:
        factory = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "open.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
            with patch.dict(
                "os.environ",
                {
                    "AEROBIM_VLM_API_BASE_URL": "https://example.invalid",
                    "AEROBIM_VLM_API_KEY": "test-key",
                },
            ):
                report = run_smoke(
                    image,
                    sheet_id="S1",
                    tenant_id="",  # empty → blocked
                    client_factory=factory,
                    allow_whole_sheet=True,
                )
        self.assertEqual(report["status"], "BLOCKED_BY_GATE")
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
