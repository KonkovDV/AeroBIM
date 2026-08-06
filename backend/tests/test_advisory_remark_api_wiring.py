"""Analyze path wires LLM advisory remark compose (KT#2 text contour).

Verdict OFF==ON must stay green after wiring. Capability is SKIPPED when the
model is unavailable — never FAILED, never flips summary.passed.
"""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class AdvisoryRemarkApiWiringTests(unittest.TestCase):
    def test_overlay_attaches_ai_generated_remarks(self) -> None:
        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks
        from aerobim.domain.llm_advisory import MockLlmProvider
        from aerobim.domain.models import (
            CapabilityState,
            FindingCategory,
            GeneratedRemark,
            Severity,
            ValidationIssue,
        )

        class _JsonMock(MockLlmProvider):
            def generate(self, request):  # type: ignore[override]
                base = super().generate(request)
                draft = {
                    "title": "Черновик AI",
                    "body": "Сформировано по детерминированной находке.",
                    "locale": "ru",
                    "evidence_refs": list(request.evidence_refs or ()),
                }
                return replace(
                    base,
                    remark_draft=json.dumps(draft, ensure_ascii=False),
                    schema_valid=True,
                    status="advisory",
                )

        issue = ValidationIssue(
            rule_id="R-WIRE-1",
            category=FindingCategory.IFC_VALIDATION,
            severity=Severity.ERROR,
            message="missing property",
            finding_id="fid-wire-1",
            origin="deterministic",
            remark=GeneratedRemark(title="template", body="template body"),
        )
        issues, capability = overlay_llm_remarks(
            (issue,),
            provider=_JsonMock(provider="mock", model="mock-model"),
            request_id="wire-1",
            locale="ru",
        )
        self.assertEqual(capability.status, CapabilityState.OK)
        self.assertEqual(len(issues), 1)
        remark = issues[0].remark
        assert remark is not None
        self.assertTrue(remark.ai_generated)
        self.assertTrue(remark.expert_confirmation_required)
        self.assertEqual(remark.title, "Черновик AI")
        # Identity fields untouched (OFF==ON signature).
        self.assertEqual(issues[0].rule_id, issue.rule_id)
        self.assertEqual(issues[0].severity, issue.severity)
        self.assertEqual(issues[0].origin, issue.origin)

    def test_overlay_capability_reason_includes_total_findings(self) -> None:
        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks
        from aerobim.domain.llm_advisory import MockLlmProvider
        from aerobim.domain.models import (
            CapabilityState,
            FindingCategory,
            GeneratedRemark,
            Severity,
            ValidationIssue,
        )

        class _JsonMock(MockLlmProvider):
            def generate(self, request):  # type: ignore[override]
                base = super().generate(request)
                draft = {
                    "title": "Черновик",
                    "body": "body",
                    "locale": "ru",
                    "evidence_refs": list(request.evidence_refs or ()),
                }
                return replace(
                    base,
                    remark_draft=json.dumps(draft, ensure_ascii=False),
                    schema_valid=True,
                    status="advisory",
                )

        issues_in = tuple(
            ValidationIssue(
                rule_id=f"R-{i}",
                category=FindingCategory.IFC_VALIDATION,
                severity=Severity.ERROR,
                message=f"m{i}",
                origin="deterministic",
                remark=GeneratedRemark(title="t", body="b"),
            )
            for i in range(5)
        )
        _issues, capability = overlay_llm_remarks(
            issues_in,
            provider=_JsonMock(provider="mock", model="mock"),
            request_id="cap-total",
            max_issues=2,
        )
        self.assertEqual(capability.status, CapabilityState.OK)
        reason = capability.reason or ""
        self.assertIn("2/2 of 5 findings", reason)
        self.assertIn("cap=2", reason)
        ai_count = sum(1 for i in _issues if i.remark and i.remark.ai_generated)
        self.assertEqual(ai_count, 2)

    def test_disabled_provider_skips_capability(self) -> None:
        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks
        from aerobim.domain.llm_advisory import DisabledLlmProvider
        from aerobim.domain.models import (
            CapabilityState,
            FindingCategory,
            GeneratedRemark,
            Severity,
            ValidationIssue,
        )

        issue = ValidationIssue(
            rule_id="R-SKIP",
            category=FindingCategory.IFC_VALIDATION,
            severity=Severity.WARNING,
            message="warn",
            origin="deterministic",
            remark=GeneratedRemark(title="t", body="b"),
        )
        issues, capability = overlay_llm_remarks(
            (issue,),
            provider=DisabledLlmProvider(),
            request_id="skip-1",
        )
        self.assertEqual(capability.status, CapabilityState.SKIPPED)
        self.assertIn("not configured", capability.reason or "")
        self.assertEqual(issues[0].remark, issue.remark)

    def test_network_off_skips_capability_keeps_verdict(self) -> None:
        """Acceptance #4: dead transport → SKIPPED, analysis completes, verdict stable."""

        from aerobim.application.services.advisory_remark_overlay import overlay_llm_remarks
        from aerobim.domain.llm_token_budget import LlmTokenBudget
        from aerobim.domain.models import (
            CapabilityState,
            FindingCategory,
            GeneratedRemark,
            Severity,
            ValidationIssue,
        )
        from aerobim.infrastructure.adapters.openai_compat_llm_provider import (
            OpenAICompatLlmProvider,
        )

        def _boom(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            raise OSError("Network unreachable")

        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:9/v1",
            model="Qwen3.6-27B",
            model_revision="test-pin",
            transport=_boom,
            budget=LlmTokenBudget(max_tokens_per_day=600_000),
            timeout_seconds=1.0,
        )
        issue = ValidationIssue(
            rule_id="R-NET",
            category=FindingCategory.IFC_VALIDATION,
            severity=Severity.ERROR,
            message="x",
            origin="deterministic",
            remark=GeneratedRemark(title="t", body="b"),
        )
        issues, capability = overlay_llm_remarks(
            (issue,),
            provider=provider,
            request_id="net-off",
        )
        self.assertEqual(capability.status, CapabilityState.SKIPPED)
        self.assertIn("skipped", (capability.reason or "").lower())
        self.assertEqual(issues[0].severity, Severity.ERROR)
        assert issues[0].remark is not None
        self.assertFalse(issues[0].remark.ai_generated)
        self.assertEqual(issues[0].remark.title, "t")

    def test_day_budget_exhaustion_is_blocked_by_policy_not_transport(self) -> None:
        """Acceptance #5: day cap → blocked_by_policy / budget_exceeded (not transport)."""

        from aerobim.domain.advisory_remark_compose import compose_remark
        from aerobim.domain.llm_token_budget import LlmTokenBudget
        from aerobim.infrastructure.adapters.openai_compat_llm_provider import (
            OpenAICompatLlmProvider,
        )

        called = {"n": 0}

        def _transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            called["n"] += 1
            return b"{}"

        budget = LlmTokenBudget(
            max_tokens_per_call=100,
            max_tokens_per_run=10_000,
            max_tokens_per_day=50,
        )
        # Pre-fill day counter past the cap.
        budget.tokens_today = 50
        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:9/v1",
            model="Qwen3.6-27B",
            model_revision="test-pin",
            transport=_transport,
            budget=budget,
        )
        result = compose_remark(
            findings=({"finding_id": "b1", "message": "m"},),
            locale="ru",
            request_id="budget-day",
            provider=provider,
            allow_synthetic_public=True,
        )
        self.assertEqual(result.status, "SKIPPED")
        self.assertEqual(result.reason, "budget_exceeded")
        self.assertEqual(called["n"], 0)
        assert result.response is not None
        self.assertEqual(result.response.status, "blocked_by_policy")

    def test_analyze_path_emits_llm_advisory_capability_and_keeps_verdict(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.llm_advisory import DisabledLlmProvider, MockLlmProvider
        from aerobim.domain.models import CapabilityState
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-baseline.json"
        if not pack_path.exists():
            self.skipTest("baseline benchmark pack missing")
        request = load_benchmark_pack(pack_path, repo_root_path=repo_root).request

        settings = Settings.from_env()
        container = bootstrap_container(settings)
        use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
        self.assertIsInstance(use_case._llm_advisory_provider, DisabledLlmProvider)

        report_off = use_case.execute(
            replace(request, request_id="wire-off", tenant_id=request.tenant_id or "tenant-fixture")
        )
        self.assertEqual(report_off.capabilities.llm_advisory.status, CapabilityState.SKIPPED)

        class _JsonMock(MockLlmProvider):
            def generate(self, llm_request):  # type: ignore[override]
                base = super().generate(llm_request)
                draft = {
                    "title": "AI draft",
                    "body": "Deterministic finding only.",
                    "locale": "ru",
                    "evidence_refs": list(llm_request.evidence_refs or ()),
                }
                return replace(
                    base,
                    remark_draft=json.dumps(draft, ensure_ascii=False),
                    schema_valid=True,
                    status="advisory",
                )

        use_case._llm_advisory_provider = _JsonMock(provider="mock", model="mock")
        report_on = use_case.execute(
            replace(request, request_id="wire-on", tenant_id=request.tenant_id or "tenant-fixture")
        )
        self.assertEqual(report_on.capabilities.llm_advisory.status, CapabilityState.OK)
        ai_remarks = [i for i in report_on.issues if i.remark and i.remark.ai_generated]
        self.assertGreater(len(ai_remarks), 0)

        off_sig = (
            report_off.summary.passed,
            report_off.summary.error_count,
            report_off.summary.warning_count,
            tuple(
                sorted(
                    (i.rule_id, i.category.value, i.severity.value, i.origin or "")
                    for i in report_off.issues
                )
            ),
        )
        on_sig = (
            report_on.summary.passed,
            report_on.summary.error_count,
            report_on.summary.warning_count,
            tuple(
                sorted(
                    (i.rule_id, i.category.value, i.severity.value, i.origin or "")
                    for i in report_on.issues
                )
            ),
        )
        self.assertEqual(off_sig, on_sig)


if __name__ == "__main__":
    unittest.main()
