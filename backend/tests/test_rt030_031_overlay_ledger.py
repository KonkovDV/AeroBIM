"""RT-030 / RT-031 — HybridRouteGate on LLM overlay + ledger fail-closed at boot."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aerobim.application.services.analyze_orchestrators import EvidenceAssembler
from aerobim.application.services.hybrid_route_gate import HybridRouteGate
from aerobim.core.config.settings import Settings
from aerobim.domain.llm_advisory import DisabledLlmProvider, MockLlmProvider
from aerobim.domain.models import (
    RequirementSource,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider
from aerobim.infrastructure.di.bootstrap import _build_llm_advisory_provider


class _Host:
    def __init__(self, *, provider, gate) -> None:
        self._llm_advisory_provider = provider
        self._hybrid_route_gate = gate
        self._remark_locale = "ru"
        self.overlay_calls = 0

    def _overlay_llm_remarks(self, issues, *, request_id: str):
        self.overlay_calls += 1
        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks

        return overlay_llm_remarks(
            tuple(issues),
            provider=self._llm_advisory_provider,
            request_id=request_id,
            locale=self._remark_locale,
        )


class Rt030OverlayGateTests(unittest.TestCase):
    def test_yandex_on_confidential_ifc_skips_overlay(self) -> None:
        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:9/v1",
            model="qwen",
            provider="yandex-ai-studio",
            model_revision="pin",
            transport=lambda *_a, **_k: b"{}",
        )
        host = _Host(provider=provider, gate=HybridRouteGate())
        assembler = EvidenceAssembler(host)  # type: ignore[arg-type]
        request = ValidationRequest(
            request_id="rt030-conf",
            ifc_path=Path("projects/customer/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        allowed, trace = assembler._evaluate_llm_overlay_gate(request)
        self.assertFalse(allowed)
        assert trace is not None
        self.assertEqual(trace["task_type"], "advisory_remark_overlay")
        self.assertEqual(trace["target"], "public")
        self.assertEqual(trace["status"], "blocked")

    def test_yandex_on_public_fixture_allows_overlay(self) -> None:
        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:9/v1",
            model="qwen",
            provider="yandex-ai-studio",
            model_revision="pin",
            transport=lambda *_a, **_k: b"{}",
        )
        host = _Host(provider=provider, gate=HybridRouteGate())
        assembler = EvidenceAssembler(host)  # type: ignore[arg-type]
        request = ValidationRequest(
            request_id="rt030-fix",
            ifc_path=Path("samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        allowed, trace = assembler._evaluate_llm_overlay_gate(request)
        self.assertTrue(allowed)
        assert trace is not None
        self.assertEqual(trace["status"], "public_masked")

    def test_missing_gate_suppresses_overlay(self) -> None:
        host = _Host(provider=MockLlmProvider(provider="mock", model="mock"), gate=None)
        assembler = EvidenceAssembler(host)  # type: ignore[arg-type]
        request = ValidationRequest(
            request_id="rt030-nogate",
            ifc_path=Path("samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        allowed, trace = assembler._evaluate_llm_overlay_gate(request)
        self.assertFalse(allowed)
        assert trace is not None
        self.assertIn("not configured", str(trace["reason"]))

    def test_disabled_provider_bypasses_gate_eval(self) -> None:
        host = _Host(provider=DisabledLlmProvider(), gate=None)
        assembler = EvidenceAssembler(host)  # type: ignore[arg-type]
        request = ValidationRequest(
            request_id="rt030-disabled",
            ifc_path=Path("samples/ifc/wall.ifc"),
            requirement_source=RequirementSource(),
            ids_path=Path("dummy.ids"),
            tenant_id="tenant-a",
        )
        allowed, trace = assembler._evaluate_llm_overlay_gate(request)
        self.assertTrue(allowed)
        self.assertIsNone(trace)


class Rt031LedgerFailClosedTests(unittest.TestCase):
    def test_ready_without_ledger_raises_in_bootstrap_builder(self) -> None:
        settings = replace(
            Settings.from_env(),
            llm_local_enabled=True,
            llm_base_url="http://127.0.0.1:9/v1",
            llm_model="Qwen3.6-27B",
            llm_model_revision="pin@test",
            llm_budget_ledger_path=None,
        )
        self.assertTrue(settings.llm_local_ready())
        with self.assertRaises(RuntimeError) as ctx:
            _build_llm_advisory_provider(settings)
        self.assertIn("BUDGET_LEDGER", str(ctx.exception))

    def test_ready_with_ledger_builds_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = replace(
                Settings.from_env(),
                llm_local_enabled=True,
                llm_base_url="http://127.0.0.1:9/v1",
                llm_model="Qwen3.6-27B",
                llm_model_revision="pin@test",
                llm_budget_ledger_path=Path(tmp) / "ledger.json",
            )
            provider = _build_llm_advisory_provider(settings)
            self.assertIsInstance(provider, OpenAICompatLlmProvider)


if __name__ == "__main__":
    unittest.main()
