"""Local Qwen / OpenAI-compat advisory remark compose (scenario 5.1)."""

from __future__ import annotations

import json
import tempfile
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
            allow_synthetic_public=True,
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
            allow_synthetic_public=True,
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
            llm_budget_ledger_path=Path(tempfile.mkdtemp()) / "llm-budget.json",
        )
        self.assertFalse(off.llm_local_ready())
        self.assertTrue(on.llm_local_ready())

        container_off = bootstrap_container(off)
        container_on = bootstrap_container(on)
        self.assertIsInstance(
            container_off.resolve(Tokens.LLM_ADVISORY_PROVIDER),
            DisabledLlmProvider,
        )
        provider_on = container_on.resolve(Tokens.LLM_ADVISORY_PROVIDER)
        self.assertIsInstance(provider_on, OpenAICompatLlmProvider)

        def _transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            draft = {
                "title": "Advisory",
                "body": "Draft",
                "locale": "ru",
                "evidence_refs": ["x"],
            }
            return json.dumps(
                {
                    "choices": [{"message": {"content": json.dumps(draft)}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                }
            ).encode("utf-8")

        provider_on._transport = _transport  # noqa: SLF001 — test seam
        use_case_on = container_on.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
        use_case_on._llm_advisory_provider = provider_on  # noqa: SLF001

        def verdict(container: object, tag: str) -> object:
            use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
            report = use_case.execute(
                replace(
                    request,
                    request_id=f"llm-offon-{tag}",
                    tenant_id=request.tenant_id or "tenant-fixture",
                )
            )
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
            "PIN_EXACT_VERSION_FROM_CATALOG_NOT_latest",
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

    def test_adapter_rejects_alibaba_even_without_from_env(self) -> None:
        with self.assertRaises(RuntimeError):
            OpenAICompatLlmProvider(
                base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
                model="qwen-max",
            )


class YandexStudioCompatTests(unittest.TestCase):
    def test_resolve_model_uri_appends_revision(self) -> None:
        from aerobim.core.config.settings import resolve_llm_model_uri

        self.assertEqual(
            resolve_llm_model_uri(
                model="gpt://b1gfolder/qwen3-235b-a22b-fp8",
                revision="v2026-08-01",
            ),
            "gpt://b1gfolder/qwen3-235b-a22b-fp8/v2026-08-01",
        )
        self.assertEqual(
            resolve_llm_model_uri(
                model="gpt://b1gfolder/qwen3-235b-a22b-fp8/latest",
                revision="v2026-08-01",
            ),
            "gpt://b1gfolder/qwen3-235b-a22b-fp8/v2026-08-01",
        )

    def test_yandex_body_uses_json_schema_omits_seed_and_sets_logging_header(self) -> None:
        captured: dict[str, object] = {}

        def transport(url: str, headers: dict[str, str], body: bytes) -> bytes:
            captured["url"] = url
            captured["headers"] = headers
            captured["body"] = json.loads(body.decode("utf-8"))
            draft = {
                "title": "t",
                "body": "b",
                "locale": "ru",
                "evidence_refs": ["x"],
            }
            return json.dumps({"choices": [{"message": {"content": json.dumps(draft)}}]}).encode(
                "utf-8"
            )

        from aerobim.domain.advisory_remark_compose import build_remark_llm_request

        provider = OpenAICompatLlmProvider(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="gpt://b1gfolder/qwen3-235b-a22b-fp8",
            model_revision="v2026-08-01",
            folder_id="b1gfolder",
            api_key="test-key",
            provider="yandex-ai-studio",
            transport=transport,
            send_seed=False,
            response_schema_mode="json_schema",
            auth_scheme="Bearer",
            extra_headers={
                "x-folder-id": "b1gfolder",
                "x-data-logging-enabled": "false",
            },
        )
        response = provider.generate(
            build_remark_llm_request(
                request_id="r",
                findings=({"finding_id": "x", "message": "m"},),
                locale="ru",
                allow_customer_data=False,
                allow_synthetic_public=True,
            )
        )
        self.assertEqual(response.status, "advisory")
        body = captured["body"]
        assert isinstance(body, dict)
        self.assertNotIn("seed", body)
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(
            body["chat_template_kwargs"],
            {"enable_thinking": False},
        )
        self.assertEqual(
            body["model"],
            "gpt://b1gfolder/qwen3-235b-a22b-fp8/v2026-08-01",
        )
        headers = captured["headers"]
        assert isinstance(headers, dict)
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(headers["x-data-logging-enabled"], "false")
        self.assertEqual(headers["x-folder-id"], "b1gfolder")
        self.assertNotEqual(headers["x-client-request-id"], "r")
        self.assertEqual(len(headers["x-client-request-id"].split("-")), 5)
        self.assertTrue(response.usage.get("data_logging_disabled"))
        self.assertFalse(response.usage.get("reproducible"))
        self.assertFalse(response.usage.get("seed_sent"))
        self.assertTrue(response.usage.get("thinking_disabled"))
        self.assertEqual(response.usage.get("vendor_model_uri"), body["model"])
        self.assertEqual(response.usage.get("internal_request_id"), "r")
        self.assertEqual(response.usage.get("client_request_id"), headers["x-client-request-id"])
        self.assertIn("prompt_sha256", response.usage)
        self.assertIn("response_sha256", response.usage)

    def test_unversioned_gpt_uri_allowed(self) -> None:
        from aerobim.core.config.settings import resolve_llm_model_uri

        self.assertEqual(
            resolve_llm_model_uri(
                model="gpt://b1gfolder/qwen3.6-35b-a3b",
                revision=None,
            ),
            "gpt://b1gfolder/qwen3.6-35b-a3b",
        )
        provider = OpenAICompatLlmProvider(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="gpt://b1gfolder/qwen3.6-35b-a3b",
            provider="yandex-ai-studio",
            transport=lambda *_a: b"{}",
        )
        self.assertEqual(provider._model, "gpt://b1gfolder/qwen3.6-35b-a3b")

    def test_reasoning_only_not_schema_deviation(self) -> None:
        from aerobim.domain.advisory_remark_compose import build_remark_llm_request, compose_remark

        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            return json.dumps(
                {
                    "model": "gpt://qwen3.6-35b-a3b/latest",
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "reasoning_content": "thinking burned the budget…",
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 512},
                }
            ).encode("utf-8")

        provider = OpenAICompatLlmProvider(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="gpt://b1gfolder/qwen3.6-35b-a3b",
            provider="yandex-ai-studio",
            transport=transport,
            disable_thinking=False,
        )
        response = provider.generate(
            build_remark_llm_request(
                request_id="r",
                findings=({"finding_id": "x"},),
                allow_synthetic_public=True,
            )
        )
        self.assertEqual(response.status, "failed")
        self.assertIn("reasoning_only", response.uncertainties)
        self.assertNotIn("schema_deviation", response.uncertainties)
        self.assertEqual(response.usage.get("vendor_model_uri"), "gpt://qwen3.6-35b-a3b/latest")
        result = compose_remark(
            findings=({"finding_id": "x"},),
            locale="ru",
            request_id="r",
            provider=provider,
            allow_synthetic_public=True,
        )
        self.assertEqual(result.status, "SKIPPED")
        self.assertEqual(result.reason, "reasoning_only")

    def test_strips_markdown_fence_around_json(self) -> None:
        from aerobim.domain.advisory_remark_compose import build_remark_llm_request

        draft = {
            "title": "t",
            "body": "b",
            "locale": "ru",
            "evidence_refs": ["x"],
        }

        def transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            fenced = "```json\n" + json.dumps(draft) + "\n```"
            return json.dumps(
                {
                    "model": "gpt://b1gfolder/qwen3.6-35b-a3b/latest",
                    "choices": [{"message": {"content": fenced}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 2},
                }
            ).encode("utf-8")

        provider = OpenAICompatLlmProvider(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="gpt://b1gfolder/qwen3.6-35b-a3b",
            provider="yandex-ai-studio",
            transport=transport,
        )
        response = provider.generate(
            build_remark_llm_request(
                request_id="r",
                findings=({"finding_id": "x"},),
                allow_synthetic_public=True,
            )
        )
        self.assertEqual(response.status, "advisory")
        self.assertTrue(response.schema_valid)

    def test_latest_alias_forbidden(self) -> None:
        from aerobim.core.config.settings import assert_llm_model_pin_no_aliases

        with self.assertRaises(RuntimeError):
            assert_llm_model_pin_no_aliases("gpt://b1g/qwen/latest")
        with self.assertRaises(RuntimeError):
            OpenAICompatLlmProvider(
                base_url="https://llm.api.cloud.yandex.net/v1",
                model="gpt://b1g/qwen/latest",
                model_revision="latest",
            )

    def test_429_retries_then_succeeds(self) -> None:
        import urllib.error

        from aerobim.domain.advisory_remark_compose import build_remark_llm_request

        calls = {"n": 0}

        def transport(url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            calls["n"] += 1
            if calls["n"] < 3:
                raise urllib.error.HTTPError(
                    url,
                    429,
                    "Too Many Requests",
                    hdrs=urllib.error.HTTPError(url, 429, "", None, None).headers,  # type: ignore[arg-type]
                    fp=None,
                )
            draft = {
                "title": "t",
                "body": "b",
                "locale": "ru",
                "evidence_refs": ["x"],
            }
            return json.dumps({"choices": [{"message": {"content": json.dumps(draft)}}]}).encode(
                "utf-8"
            )

        # Build a real HTTPError without nested construction.
        def transport2(url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            calls["n"] += 1
            if calls["n"] < 3:
                err = urllib.error.HTTPError(url, 429, "Too Many Requests", None, None)
                raise err
            draft = {
                "title": "t",
                "body": "b",
                "locale": "ru",
                "evidence_refs": ["x"],
            }
            return json.dumps({"choices": [{"message": {"content": json.dumps(draft)}}]}).encode(
                "utf-8"
            )

        calls["n"] = 0
        provider = OpenAICompatLlmProvider(
            base_url="https://llm.api.cloud.yandex.net/v1",
            model="gpt://b1g/qwen/v1",
            model_revision="v1",
            transport=transport2,
            send_seed=False,
            response_schema_mode="json_schema",
            retries_429=3,
            max_concurrent=2,
        )
        response = provider.generate(
            build_remark_llm_request(
                request_id="r429",
                findings=({"finding_id": "x", "message": "m"},),
                allow_customer_data=False,
                allow_synthetic_public=True,
            )
        )
        self.assertEqual(response.status, "advisory")
        self.assertEqual(calls["n"], 3)


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
            allow_synthetic_public=True,
        )
        response = provider.generate(request)
        self.assertEqual(response.status, "blocked_by_policy")
        self.assertTrue(any("budget_exceeded" in u for u in response.uncertainties))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
