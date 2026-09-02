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
import os
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
from aerobim.domain.models import DrawingSource
from aerobim.domain.vlm_grounding import ground_vlm_drawing_response
from aerobim.infrastructure.adapters.vlm_advisory_client import (
    VlmAdvisoryClient,
    VlmAdvisoryError,
    VlmReadResult,
    profile_for,
)
from aerobim.infrastructure.adapters.vlm_drawing_pipeline import VlmDrawingPipeline


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

    def test_one_invalid_region_fails_whole_drawing_response(self) -> None:
        """Re-Audit #8 wording: drawing-schema fail is whole-response, not per-region."""

        raw = {
            "regions": [
                {"bbox": [10, 20, 100, 60], "confidence": 0.91},
                {"bbox": [1, 2, 3], "confidence": 0.9},
            ]
        }
        result = ground_vlm_drawing_response(raw, sheet_id="S1", model_id="kimi-k3")
        self.assertFalse(result.parse_ok)
        self.assertEqual(result.regions, ())

    def test_nan_confidence_abstains_not_high(self) -> None:
        # Red Team: NaN must not slip past the abstention gate as high confidence.
        raw = {"regions": [{"bbox": [1, 1, 2, 2], "confidence": float("nan")}]}
        result = ground_vlm_drawing_response(raw, sheet_id="S1", model_id="kimi-k3")
        self.assertTrue(result.parse_ok)
        self.assertEqual(result.regions[0].confidence, 0.0)
        self.assertTrue(result.regions[0].hitl_required)

    def test_nonfinite_bbox_fails_closed(self) -> None:
        for bad in (float("inf"), float("nan"), float("-inf")):
            raw = {"regions": [{"bbox": [bad, 1, 2, 2], "confidence": 0.9}]}
            result = ground_vlm_drawing_response(raw, sheet_id="S1", model_id="kimi-k3")
            self.assertFalse(result.parse_ok, bad)
            self.assertEqual(result.regions, ())


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

    def _client(self, transport) -> VlmAdvisoryClient:
        return VlmAdvisoryClient(
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
        self.assertIn("regions", parsed.content)
        self.assertEqual(captured["url"], "https://kimi.example.com/v1/chat/completions")
        self.assertEqual(captured["auth"], "Bearer secret-key-abc")

    def test_repr_redacts_api_key(self) -> None:
        client = self._client(lambda *a, **k: b"{}")
        self.assertNotIn("secret-key-abc", repr(client))

    def test_missing_choices_raises(self) -> None:
        client = self._client(lambda *a, **k: b'{"no":"choices"}')
        with self.assertRaises(VlmAdvisoryError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_non_json_content_raises(self) -> None:
        env = json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode("utf-8")
        client = self._client(lambda *a, **k: env)
        with self.assertRaises(VlmAdvisoryError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_requires_base_url_and_key(self) -> None:
        with self.assertRaises(VlmAdvisoryError):
            VlmAdvisoryClient(base_url="", api_key="k")
        with self.assertRaises(VlmAdvisoryError):
            VlmAdvisoryClient(base_url="https://x", api_key="")

    def test_default_transport_blocks_private_ip_ssrf(self) -> None:
        # No transport injected → default transport uses the SSRF guard.
        client = VlmAdvisoryClient(base_url="https://127.0.0.1", api_key="k")
        with self.assertRaises(UnsafeOutboundUrlError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_default_transport_caps_response_size(self) -> None:
        oversized = b"x" * 64
        client = VlmAdvisoryClient(
            base_url="https://kimi.example.com/v1",
            api_key="k",
            max_response_bytes=8,
            allowed_hosts=frozenset({"kimi.example.com"}),
        )
        with patch.object(outbound_url, "safe_urlopen", lambda *a, **k: _FakeResp(oversized)):
            with self.assertRaises(VlmAdvisoryError):
                client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_default_transport_rejects_non_allowlisted_host(self) -> None:
        with self.assertRaises(RuntimeError):
            VlmAdvisoryClient(
                base_url="https://evil.example.com/v1",
                api_key="k",
            )

    def test_nan_in_structured_content_rejected(self) -> None:
        # Red Team: json.loads accepts the NaN literal by default; the client must
        # reject non-finite JSON constants at the boundary.
        content_with_nan = '{"regions":[{"bbox":[1,2,3,4],"confidence":NaN}]}'
        env = json.dumps({"choices": [{"message": {"content": content_with_nan}}]}).encode("utf-8")
        client = self._client(lambda *a, **k: env)
        with self.assertRaises(VlmAdvisoryError):
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")

    def test_content_json_fence_parses(self) -> None:
        # Real servers wrap JSON in ```json fences even under json_object.
        content = '```json\n{"regions": [{"bbox": [1,2,3,4], "confidence": 0.9}]}\n```'
        env = json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")
        client = self._client(lambda *a, **k: env)
        parsed = client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        self.assertIn("regions", parsed.content)

    def test_content_as_dict_object_parses(self) -> None:
        # Some OpenAI-compatible servers return the structured object directly.
        env = json.dumps({"choices": [{"message": {"content": {"regions": []}}}]}).encode("utf-8")
        client = self._client(lambda *a, **k: env)
        parsed = client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        self.assertEqual(parsed.content, {"regions": []})


class VlmProfileAndContractTests(unittest.TestCase):
    def test_kimi_k3_profile_shapes(self) -> None:
        p = profile_for("kimi-k3")
        self.assertFalse(p.send_temperature)
        self.assertEqual(p.response_format["type"], "json_schema")
        self.assertTrue(p.supports_reasoning_effort)
        self.assertTrue(p.disable_server_tools)
        self.assertEqual(p.determinism_basis, "sampling_fixed_by_service")

    def test_vllm_profile_shapes(self) -> None:
        p = profile_for("kimi-vl-3b")
        self.assertTrue(p.send_temperature)
        self.assertEqual(p.response_format["type"], "json_object")
        self.assertFalse(p.supports_reasoning_effort)
        self.assertEqual(p.determinism_basis, "temperature_zero")

    def _capture_body(self, model: str) -> dict:
        captured: dict[str, object] = {}
        ok = json.dumps({"choices": [{"message": {"content": '{"regions":[]}'}}]}).encode("utf-8")

        def transport(url: str, headers: dict[str, str], body: bytes) -> bytes:
            captured["body"] = json.loads(body.decode("utf-8"))
            return ok

        client = VlmAdvisoryClient(
            base_url="https://x/v1",
            api_key="k",
            model=model,
            reasoning_effort="high",
            transport=transport,
        )
        client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        return captured["body"]  # type: ignore[return-value]

    def test_kimi_k3_payload_no_temp_reasoning_tools_empty(self) -> None:
        body = self._capture_body("kimi-k3")
        self.assertNotIn("temperature", body)
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(body["reasoning_effort"], "high")
        self.assertEqual(body["tools"], [])

    def test_vllm_payload_sends_temperature_no_reasoning(self) -> None:
        body = self._capture_body("kimi-vl-3b")
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["response_format"]["type"], "json_object")
        self.assertNotIn("reasoning_effort", body)

    def test_truncated_finish_reason_classified(self) -> None:
        env = json.dumps(
            {"choices": [{"finish_reason": "length", "message": {"content": '{"regions"'}}]}
        ).encode("utf-8")
        client = VlmAdvisoryClient(
            base_url="https://x/v1", api_key="k", transport=lambda *a, **k: env
        )
        with self.assertRaises(VlmAdvisoryError) as ctx:
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        self.assertEqual(ctx.exception.reason_code, "TRUNCATED")

    def test_empty_content_with_reasoning_classified(self) -> None:
        env = json.dumps(
            {"choices": [{"message": {"content": "", "reasoning_content": "thinking"}}]}
        ).encode("utf-8")
        client = VlmAdvisoryClient(
            base_url="https://x/v1", api_key="k", transport=lambda *a, **k: env
        )
        with self.assertRaises(VlmAdvisoryError) as ctx:
            client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        self.assertEqual(ctx.exception.reason_code, "EMPTY_CONTENT")

    def test_usage_and_determinism_basis_captured(self) -> None:
        env = json.dumps(
            {
                "choices": [{"message": {"content": '{"regions":[]}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }
        ).encode("utf-8")
        client = VlmAdvisoryClient(
            base_url="https://x/v1", api_key="k", model="kimi-k3", transport=lambda *a, **k: env
        )
        result = client.read_drawing(b"x", media_type="image/png", sheet_id="S1", prompt="p")
        self.assertEqual(result.usage["prompt_tokens"], 10)
        self.assertEqual(result.determinism_basis, "sampling_fixed_by_service")

    def test_read_region_uses_observations_schema(self) -> None:
        captured: dict[str, object] = {}
        ok = json.dumps(
            {"choices": [{"message": {"content": '{"readable":true,"observations":[]}'}}]}
        ).encode("utf-8")

        def transport(url: str, headers: dict[str, str], body: bytes) -> bytes:
            captured["body"] = json.loads(body.decode("utf-8"))
            return ok

        client = VlmAdvisoryClient(
            base_url="https://x/v1", api_key="k", model="kimi-k3", transport=transport
        )
        res = client.read_region(
            b"x", media_type="image/png", sheet_id="AR-01", region_id="stamp", prompt="p"
        )
        body = captured["body"]
        assert isinstance(body, dict)
        self.assertEqual(
            body["response_format"]["json_schema"]["name"], "aerobim_region_observations"
        )
        self.assertIn("AR-01#stamp", body["messages"][1]["content"][0]["text"])
        self.assertIn("observations", res.content)


class KimiConfigGateTests(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        self.assertFalse(_settings().vlm_advisory_ready())

    def test_enabled_but_unconfigured_is_not_ready(self) -> None:
        self.assertFalse(_settings(vlm_enabled=True).vlm_advisory_ready())

    def test_dev_open_data_ready_when_configured(self) -> None:
        ready = _settings(
            vlm_enabled=True,
            vlm_api_base_url="https://kimi.example.com/v1",
            vlm_api_key="k",
            signoff_profile="development",
        ).vlm_advisory_ready()
        self.assertTrue(ready)

    def test_customer_profile_hard_disables_public_api(self) -> None:
        for profile in ("samolet_pilot", "production"):
            ready = _settings(
                vlm_enabled=True,
                vlm_api_base_url="https://kimi.example.com/v1",
                vlm_api_key="k",
                signoff_profile=profile,
            ).vlm_advisory_ready()
            self.assertFalse(ready, profile)

    def test_yandex_with_default_kimi_model_is_not_ready(self) -> None:
        ready = _settings(
            vlm_enabled=True,
            vlm_api_base_url="https://llm.api.cloud.yandex.net/v1",
            vlm_api_key="k",
            vlm_model="kimi-k3",
            signoff_profile="development",
            llm_provider="yandex-ai-studio",
        ).vlm_advisory_ready()
        self.assertFalse(ready)

    def test_yandex_provider_with_ip_host_and_kimi_is_not_ready(self) -> None:
        """IP/proxy URL must not bypass refuse when provider is Yandex."""

        ready = _settings(
            vlm_enabled=True,
            vlm_api_base_url="https://203.0.113.10/v1",
            vlm_api_key="k",
            vlm_model="kimi-k3",
            signoff_profile="development",
            llm_provider="yandex-ai-studio",
        ).vlm_advisory_ready()
        self.assertFalse(ready)

    def test_yandex_with_pinned_qwen_model_is_ready(self) -> None:
        ready = _settings(
            vlm_enabled=True,
            vlm_api_base_url="https://llm.api.cloud.yandex.net/v1",
            vlm_api_key="k",
            vlm_model="gpt://folder/qwen3.6-35b-a3b",
            signoff_profile="development",
            llm_provider="yandex-ai-studio",
        ).vlm_advisory_ready()
        self.assertTrue(ready)


class _CountingReader:
    def __init__(self, response: dict | None = None, raise_exc: Exception | None = None) -> None:
        self.calls = 0
        self._response = response if response is not None else {"regions": []}
        self._raise = raise_exc

    def read_drawing(
        self, image_bytes: bytes, *, media_type: str, sheet_id: str, prompt: str
    ) -> VlmReadResult:
        self.calls += 1
        if self._raise is not None:
            raise self._raise
        return VlmReadResult(content=self._response, usage={}, determinism_basis="test")


def _png_source(tmp: str, name: str = "AR-01.png") -> DrawingSource:
    path = Path(tmp) / name
    path.write_bytes(b"\x89PNG\r\n\x1a\n fake image bytes")
    return DrawingSource(path=path, sheet_id="AR-01")


class KimiVlmPipelineTests(unittest.TestCase):
    def test_not_ready_degrades_without_calling_vlm(self) -> None:
        reader = _CountingReader()
        pipeline = VlmDrawingPipeline(reader, ready=False)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertEqual(reader.calls, 0)
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "unavailable")

    def test_ocr_only_mode_does_not_call_vlm(self) -> None:
        reader = _CountingReader()
        pipeline = VlmDrawingPipeline(reader, ready=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="ocr_only")
        self.assertEqual(reader.calls, 0)
        self.assertTrue(result.degraded)

    def test_valid_read_yields_candidate_regions_always_degraded(self) -> None:
        reader = _CountingReader(
            {"regions": [{"bbox": [1, 2, 3, 4], "text": "AR-01", "confidence": 0.9}]}
        )
        pipeline = VlmDrawingPipeline(reader, ready=True, model_id="kimi-k3")
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertEqual(reader.calls, 1)
        self.assertEqual(len(result.regions), 1)
        self.assertEqual(result.annotations, ())
        self.assertEqual(result.pipeline_mode_used, "vlm_candidate")
        self.assertTrue(result.degraded)  # candidates never verified CV
        self.assertIn("cv_human_level remains", result.reason or "")

    def test_schema_deviation_fails_closed(self) -> None:
        reader = _CountingReader({"no_regions": True})
        pipeline = VlmDrawingPipeline(reader, ready=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertEqual(reader.calls, 1)
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "unavailable")

    def test_client_error_fails_closed(self) -> None:
        reader = _CountingReader(raise_exc=VlmAdvisoryError("boom"))
        pipeline = VlmDrawingPipeline(reader, ready=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "unavailable")

    def test_unsupported_suffix_degrades_before_read(self) -> None:
        reader = _CountingReader()
        pipeline = VlmDrawingPipeline(reader, ready=True)
        source = DrawingSource(path=Path("nonexistent/plan.pdf"), sheet_id="S1")
        result = pipeline.analyze(source, mode="auto")
        self.assertEqual(reader.calls, 0)
        self.assertTrue(result.degraded)

    def test_end_to_end_with_real_client_fake_transport(self) -> None:
        envelope = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"regions": [{"bbox": [0, 0, 9, 9], "confidence": 0.4}]}
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")
        client = VlmAdvisoryClient(
            base_url="https://kimi.example.com/v1",
            api_key="k",
            transport=lambda url, headers, body: envelope,
        )
        pipeline = VlmDrawingPipeline(client, ready=True)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertEqual(len(result.regions), 1)
        self.assertTrue(result.regions[0].hitl_required)  # 0.4 < 0.6 → abstain
        self.assertTrue(result.degraded)

    def test_oversized_image_degrades_without_reading(self) -> None:
        # Red Team: size gate must trip on stat() before read_bytes (OOM guard);
        # the VLM is not called.
        reader = _CountingReader({"regions": []})
        pipeline = VlmDrawingPipeline(reader, ready=True, max_image_bytes=4)
        with tempfile.TemporaryDirectory() as tmp:
            result = pipeline.analyze(_png_source(tmp), mode="auto")
        self.assertEqual(reader.calls, 0)
        self.assertTrue(result.degraded)
        self.assertEqual(result.pipeline_mode_used, "unavailable")


class KimiAdvisorySmokeTests(unittest.TestCase):
    def test_not_run_without_credentials(self) -> None:
        from aerobim.tools.vlm_advisory_smoke import run_smoke

        with patch.dict(os.environ, {"AEROBIM_VLM_API_BASE_URL": "", "AEROBIM_VLM_API_KEY": ""}):
            report = run_smoke(Path("nonexistent.png"), sheet_id="S1")
        self.assertEqual(report["status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
