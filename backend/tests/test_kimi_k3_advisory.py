"""Kimi K3 advisory wave (2026-07-27) — Red Team regression tests.

Invariants under test:
- VLM output is a *candidate* only; grounding never yields a verdict (ADR-001).
- Structured output is fail-closed on schema deviation (arXiv:2606.09395).
- Uncalibrated confidence → clamp + abstention→HITL (VL-Calibration ACL 2026).
- The advisory tool contract can never change the verdict; it is not an agent step.
- The client is SSRF-guarded, byte-capped, and never leaks the API key.
- Config is fail-closed and hard-disabled on customer (pilot/production) profiles.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aerobim.core.config.settings import Settings
from aerobim.core.security import outbound_url
from aerobim.core.security.outbound_url import UnsafeOutboundUrlError
from aerobim.domain.ai_tool_registry import (
    advisory_trace_record,
    allowed_agent_tool_names,
    lookup_advisory_tool,
)
from aerobim.domain.vlm_grounding import ground_vlm_drawing_response
from aerobim.infrastructure.adapters.kimi_k3_advisory_client import (
    KimiAdvisoryError,
    KimiK3AdvisoryClient,
)


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "application_name": "test",
        "environment": "development",
        "host": "127.0.0.1",
        "port": 8080,
        "storage_dir": Path(tempfile.mkdtemp()) / "var",
        "debug": True,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


class VlmGroundingTests(unittest.TestCase):
    def test_valid_response_grounds_candidates(self) -> None:
        raw = {
            "coordinate_system": "page-pixel",
            "regions": [
                {"bbox": [10, 20, 100, 60], "text": "AR-01", "confidence": 0.91},
                {"bbox": [0, 0, 50, 50], "text": "rev 2", "confidence": 0.8},
            ],
        }
        result = ground_vlm_drawing_response(raw, sheet_id="AR-01", model_id="kimi-k3")
        self.assertTrue(result.parse_ok)
        self.assertEqual(len(result.regions), 2)
        self.assertEqual(result.hitl_count, 0)
        self.assertTrue(all(r.modality == "vlm" for r in result.regions))
        self.assertIn("vlm:kimi-k3", result.evidence_refs)

    def test_low_confidence_abstains_to_hitl(self) -> None:
        raw = {"regions": [{"bbox": [1, 1, 2, 2], "confidence": 0.3}]}
        result = ground_vlm_drawing_response(
            raw, sheet_id="S1", model_id="kimi-k3", min_confidence=0.6
        )
        self.assertTrue(result.parse_ok)
        self.assertEqual(result.hitl_count, 1)
        self.assertTrue(result.regions[0].hitl_required)
        self.assertIn("uncalibrated", result.regions[0].hitl_reason or "")

    def test_confidence_is_clamped(self) -> None:
        raw = {
            "regions": [
                {"bbox": [1, 1, 2, 2], "confidence": 5.0},
                {"bbox": [1, 1, 2, 2], "confidence": -3.0},
                {"bbox": [1, 1, 2, 2], "confidence": "not-a-number"},
            ]
        }
        result = ground_vlm_drawing_response(raw, sheet_id="S1", model_id="kimi-k3")
        confidences = [r.confidence for r in result.regions]
        self.assertEqual(confidences[0], 1.0)
        self.assertEqual(confidences[1], 0.0)
        self.assertEqual(confidences[2], 0.0)

    def test_schema_deviation_fails_closed(self) -> None:
        for bad in (
            "not-an-object",
            {"no_regions": True},
            {"regions": "not-a-list"},
            {"regions": ["not-an-object"]},
            {"regions": [{"bbox": [1, 2, 3]}]},  # 3-number bbox
            {"regions": [{"bbox": "nope"}]},
        ):
            result = ground_vlm_drawing_response(bad, sheet_id="S1", model_id="kimi-k3")
            self.assertFalse(result.parse_ok, bad)
            self.assertEqual(result.regions, ())
            self.assertIsNotNone(result.reason)


class DrawingVlmToolContractTests(unittest.TestCase):
    def test_tool_registered_and_cannot_change_verdict(self) -> None:
        contract = lookup_advisory_tool("drawing_vlm_read")
        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertFalse(contract.can_change_verdict)
        self.assertTrue(contract.evidence_required)

    def test_not_an_agent_orchestrator_step(self) -> None:
        # drawing_vlm_read is invoked directly by the pipeline, not by the agent
        # step loop; the agent allowlist stays at 8 (regression guard).
        names = allowed_agent_tool_names()
        self.assertNotIn("drawing_vlm_read", names)
        self.assertEqual(len(names), 8)

    def test_trace_requires_evidence_within_one_step(self) -> None:
        with self.assertRaises(ValueError):
            advisory_trace_record(
                tool_name="drawing_vlm_read",
                request_id="req-1",
                steps=1,
                evidence_refs=(),
                payload={},
            )
        row = advisory_trace_record(
            tool_name="drawing_vlm_read",
            request_id="req-1",
            steps=1,
            evidence_refs=("vlm:kimi-k3",),
            payload={"regions": 2},
        )
        self.assertFalse(row["can_change_verdict"])


class _FakeResp:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._data
        return self._data[:size]


class KimiClientTests(unittest.TestCase):
    def _envelope(self, content_obj: dict) -> bytes:
        return json.dumps({"choices": [{"message": {"content": json.dumps(content_obj)}}]}).encode(
            "utf-8"
        )

    def _client(self, transport) -> KimiK3AdvisoryClient:  # noqa: ANN001
        return KimiK3AdvisoryClient(
            base_url="https://kimi.example.com/v1",
            api_key="secret-key-abc",
            model="kimi-k3",
            transport=transport,
        )

    def test_read_drawing_parses_structured_content(self) -> None:
        captured: dict[str, object] = {}

        def transport(url: str, headers: dict[str, str], body: bytes) -> bytes:
            captured["url"] = url
            captured["auth"] = headers.get("Authorization")
            return self._envelope({"regions": [{"bbox": [1, 2, 3, 4], "confidence": 0.9}]})

        client = self._client(transport)
        parsed = client.read_drawing(
            b"\x89PNG", media_type="image/png", sheet_id="AR-01", prompt="read title block"
        )
        self.assertIn("regions", parsed)
        self.assertEqual(captured["url"], "https://kimi.example.com/v1/chat/completions")
        self.assertEqual(captured["auth"], "Bearer secret-key-abc")

    def test_repr_redacts_api_key(self) -> None:
        client = self._client(lambda *a, **k: b"{}")
        self.assertNotIn("secret-key-abc", repr(client))

    def test_missing_choices_raises(self) -> None:
        client = self._client(lambda *a, **k: b'{"no":"choices"}')
        with self.assertRaises(KimiAdvisoryError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_non_json_content_raises(self) -> None:
        env = json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode("utf-8")
        client = self._client(lambda *a, **k: env)
        with self.assertRaises(KimiAdvisoryError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_requires_base_url_and_key(self) -> None:
        with self.assertRaises(KimiAdvisoryError):
            KimiK3AdvisoryClient(base_url="", api_key="k")
        with self.assertRaises(KimiAdvisoryError):
            KimiK3AdvisoryClient(base_url="https://x", api_key="")

    def test_default_transport_blocks_private_ip_ssrf(self) -> None:
        # No transport injected → default transport uses the SSRF guard.
        client = KimiK3AdvisoryClient(base_url="https://127.0.0.1", api_key="k")
        with self.assertRaises(UnsafeOutboundUrlError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_default_transport_caps_response_size(self) -> None:
        oversized = b"x" * 64
        client = KimiK3AdvisoryClient(
            base_url="https://kimi.example.com/v1",
            api_key="k",
            max_response_bytes=8,
        )
        with patch.object(outbound_url, "safe_urlopen", lambda *a, **k: _FakeResp(oversized)):
            with self.assertRaises(KimiAdvisoryError):
                client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")


class KimiConfigGateTests(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        self.assertFalse(_settings().kimi_advisory_ready())

    def test_enabled_but_unconfigured_is_not_ready(self) -> None:
        self.assertFalse(_settings(kimi_k3_enabled=True).kimi_advisory_ready())

    def test_dev_open_data_ready_when_configured(self) -> None:
        ready = _settings(
            kimi_k3_enabled=True,
            kimi_api_base_url="https://kimi.example.com/v1",
            kimi_api_key="k",
            signoff_profile="development",
        ).kimi_advisory_ready()
        self.assertTrue(ready)

    def test_customer_profile_hard_disables_public_api(self) -> None:
        for profile in ("samolet_pilot", "production"):
            ready = _settings(
                kimi_k3_enabled=True,
                kimi_api_base_url="https://kimi.example.com/v1",
                kimi_api_key="k",
                signoff_profile=profile,
            ).kimi_advisory_ready()
            self.assertFalse(ready, profile)


if __name__ == "__main__":
    unittest.main()
