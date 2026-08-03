"""Local Qwen / OpenAI-compat advisory remark compose (scenario 5.1)."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from aerobim.core.config.settings import Settings
from aerobim.core.di.tokens import Tokens
from aerobim.domain.advisory_remark_compose import (
    build_remark_llm_request,
    finding_payload_from_issue,
    parse_remark_response,
)
from aerobim.domain.llm_advisory import DisabledLlmProvider
from aerobim.domain.models import FindingCategory, Severity, ValidationIssue
from aerobim.infrastructure.adapters.openai_compat_llm_provider import OpenAICompatLlmProvider
from aerobim.infrastructure.di.bootstrap import bootstrap_container
from aerobim.tools.compose_advisory_remark import compose_from_findings


class OpenAICompatLlmProviderTests(unittest.TestCase):
    def test_schema_guard_and_usage_pin(self) -> None:
        draft = {
            "title": "Нарушение REI",
            "body": "По детерминированной находке требуется устранение.",
            "locale": "ru",
            "evidence_refs": ["f-1"],
        }

        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            payload = {
                "choices": [{"message": {"content": json.dumps(draft, ensure_ascii=False)}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22},
            }
            return json.dumps(payload).encode("utf-8")

        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:8000/v1",
            model="Qwen3.6-27B",
            provider="qwen-local",
            model_sha256="abc123",
            transport=transport,
        )
        request = build_remark_llm_request(
            request_id="t1",
            findings=({"finding_id": "f-1", "message": "REI missing"},),
            locale="ru",
        )
        response = provider.generate(request)
        self.assertEqual(response.status, "advisory")
        self.assertTrue(response.schema_valid)
        self.assertEqual(response.usage.get("model_sha256"), "abc123")
        remark = parse_remark_response(response, locale="ru", fallback_evidence=("f-1",))
        self.assertTrue(remark.ai_generated)
        self.assertTrue(remark.expert_confirmation_required)
        self.assertIn("REI", remark.title)

    def test_schema_deviation_fail_closed(self) -> None:
        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            return json.dumps({"choices": [{"message": {"content": "not-json-remark"}}]}).encode(
                "utf-8"
            )

        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:8000/v1",
            model="Qwen3.6-27B",
            transport=transport,
        )
        request = build_remark_llm_request(
            request_id="t2",
            findings=({"finding_id": "f-2"},),
        )
        response = provider.generate(request)
        self.assertEqual(response.status, "failed")
        self.assertFalse(response.schema_valid)


class AdvisoryRemarkComposeDomainTests(unittest.TestCase):
    def test_finding_payload_excludes_file_paths(self) -> None:
        issue = ValidationIssue(
            rule_id="R1",
            category=FindingCategory.IFC_VALIDATION,
            severity=Severity.ERROR,
            message="missing",
            finding_id="fid-1",
            source_id="src-1",
            evidence_refs=("e1",),
        )
        payload = finding_payload_from_issue(issue)
        self.assertEqual(payload["finding_id"], "fid-1")
        blob = json.dumps(payload)
        self.assertNotIn(".ifc", blob)
        self.assertNotIn(".pdf", blob)


class LlmLocalOffEqualsOnTests(unittest.TestCase):
    def test_llm_local_flag_does_not_change_verdict(self) -> None:
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-baseline.json"
        if not pack_path.exists():
            self.skipTest("baseline benchmark pack missing")
        request = load_benchmark_pack(pack_path, repo_root_path=repo_root).request

        off = Settings.from_env()
        on = replace(
            off,
            llm_local_enabled=True,
            llm_base_url="http://127.0.0.1:9/v1",
            llm_model="Qwen3.6-27B",
            llm_model_revision="qwen3.6-27b@test-pin",
            llm_model_sha256="deadbeef",
        )
        self.assertFalse(off.llm_local_ready())
        self.assertTrue(on.llm_local_ready())

        container_off = bootstrap_container(off)
        container_on = bootstrap_container(on)
        self.assertIsInstance(
            container_off.resolve(Tokens.LLM_ADVISORY_PROVIDER),
            DisabledLlmProvider,
        )
        self.assertIsInstance(
            container_on.resolve(Tokens.LLM_ADVISORY_PROVIDER),
            OpenAICompatLlmProvider,
        )

        def verdict(container: object, tag: str) -> object:
            use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
            report = use_case.execute(replace(request, request_id=f"llm-offon-{tag}"))
            signature = tuple(
                sorted(
                    (
                        issue.rule_id,
                        issue.category.value,
                        issue.severity.value,
                        issue.origin or "",
                    )
                    for issue in report.issues
                )
            )
            return (
                report.summary.passed,
                report.summary.error_count,
                report.summary.warning_count,
                signature,
            )

        self.assertEqual(verdict(container_off, "off"), verdict(container_on, "on"))


class ComposeToolTests(unittest.TestCase):
    def test_compose_skipped_when_disabled(self) -> None:
        result = compose_from_findings(
            findings=({"finding_id": "x", "message": "m"},),
            locale="ru",
            request_id="r",
            provider=DisabledLlmProvider(),
        )
        self.assertEqual(result["status"], "SKIPPED")

    def test_compose_ok_with_mock_transport_provider(self) -> None:
        draft = {
            "title": "Conflict",
            "body": "Deterministic finding requires review.",
            "locale": "en",
            "evidence_refs": ["x"],
        }

        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            return json.dumps({"choices": [{"message": {"content": json.dumps(draft)}}]}).encode(
                "utf-8"
            )

        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:8000/v1",
            model="Qwen3.6-27B",
            transport=transport,
        )
        result = compose_from_findings(
            findings=({"finding_id": "x", "message": "m", "evidence_refs": ["x"]},),
            locale="en",
            request_id="r",
            provider=provider,
            settings=Settings.from_env(),
        )
        self.assertEqual(result["status"], "OK")
        self.assertTrue(result["ai_generated"])
        self.assertEqual(result["verdict_impact"], "none")
        self.assertIn("audit_event", result)
        self.assertEqual(result["audit_event"]["task_type"], "compose_advisory_remark")
        self.assertIn("usage", result["audit_event"])


class ProviderConfigSampleTests(unittest.TestCase):
    def test_sample_config_has_local_studio_and_forbidden_cloud(self) -> None:
        path = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "hybrid"
            / "provider-config-qwen-local.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("private_qwen_local", data["profiles"])
        self.assertIn("private_yandex_ai_studio", data["profiles"])
        self.assertIn("public_qwen38_max", data["profiles"])
        self.assertEqual(
            data["profiles"]["private_yandex_ai_studio"]["model_revision"],
            "yandex://ai-studio/qwen3-235b@2026-08",
        )
        self.assertEqual(data["tier_defaults"]["private"], "private_qwen_local")
        self.assertIn("public_qwen38_max", data["forbidden_defaults"])
        self.assertIn("private_yandex_ai_studio", data["forbidden_defaults"])
        self.assertIn("OCR", data["grant_split"]["gpu_t4_use"])
        from aerobim.domain.hybrid.model_router import ProviderRegistry

        ProviderRegistry.from_config(data)


class LlmHostAllowlistTests(unittest.TestCase):
    def test_alibaba_host_forbidden(self) -> None:
        from aerobim.core.config.settings import (
            _DEFAULT_LLM_ALLOWED_HOSTS,
            assert_llm_base_host_allowed,
        )

        with self.assertRaises(RuntimeError):
            assert_llm_base_host_allowed(
                "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                _DEFAULT_LLM_ALLOWED_HOSTS,
            )

    def test_yandex_studio_host_allowed(self) -> None:
        from aerobim.core.config.settings import (
            _DEFAULT_LLM_ALLOWED_HOSTS,
            assert_llm_base_host_allowed,
        )

        assert_llm_base_host_allowed(
            "https://ai.api.cloud.yandex.net/v1",
            _DEFAULT_LLM_ALLOWED_HOSTS,
        )


class LlmTokenBudgetTests(unittest.TestCase):
    def test_per_call_and_per_run_fail_closed(self) -> None:
        from aerobim.domain.llm_token_budget import LlmTokenBudget

        budget = LlmTokenBudget(
            max_tokens_per_call=100,
            max_tokens_per_run=150,
            max_tokens_per_day=10_000,
        )
        self.assertEqual(budget.check_before(estimated_tokens=101), "budget_exceeded:per_call")

        budget2 = LlmTokenBudget(
            max_tokens_per_call=1000,
            max_tokens_per_run=100,
            max_tokens_per_day=10_000,
        )
        budget2.record(prompt_tokens=80, completion_tokens=10)
        self.assertEqual(budget2.check_before(estimated_tokens=20), "budget_exceeded:per_run")

    def test_provider_blocks_before_transport(self) -> None:
        from aerobim.domain.llm_token_budget import LlmTokenBudget

        calls: list[int] = []

        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            calls.append(1)
            raise AssertionError("transport must not run when budget blocks")

        provider = OpenAICompatLlmProvider(
            base_url="http://127.0.0.1:8000/v1",
            model="Qwen3.6-27B",
            transport=transport,
            budget=LlmTokenBudget(
                max_tokens_per_call=10, max_tokens_per_run=10, max_tokens_per_day=10
            ),
            max_completion_tokens=8,
        )
        request = build_remark_llm_request(
            request_id="budget",
            findings=({"finding_id": "f", "message": "x" * 200},),
        )
        response = provider.generate(request)
        self.assertEqual(response.status, "blocked_by_policy")
        self.assertTrue(any("budget_exceeded" in u for u in response.uncertainties))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
