"""Advisory OFF==ON invariant on the real AnalyzeProjectPackageUseCase path (§0.3/§7).

Toggling ``kimi_advisory_ready()`` must NOT change ``summary.passed`` or the
persisted verdict issues. The advisory VLM is a separate DI token deliberately
not consumed by the verdict path; this test is the regression guard that proves
the flag toggles advisory availability while the deterministic verdict is
byte-identical.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class AdvisoryVlmOffEqualsOnTests(unittest.TestCase):
    def test_kimi_flag_does_not_change_verdict_on_uc_path(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.adapters.ocr_fallback_multimodal_drawing_pipeline import (
            OcrFallbackMultimodalDrawingPipeline,
        )
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-baseline.json"
        if not pack_path.exists():
            self.skipTest("baseline benchmark pack missing")
        request = load_benchmark_pack(pack_path, repo_root_path=repo_root).request

        off = Settings.from_env()
        # replace() bypasses from_env's SSRF boot gate (no network); dev profile
        # keeps kimi_advisory_ready() unblocked.
        on = replace(
            off,
            kimi_k3_enabled=True,
            kimi_api_base_url="https://vlm.example.com/v1",
            kimi_api_key="test-key",
        )
        # The flag must actually toggle — otherwise this test is vacuous.
        self.assertFalse(off.kimi_advisory_ready())
        self.assertTrue(on.kimi_advisory_ready())

        container_off = bootstrap_container(off)
        container_on = bootstrap_container(on)

        # Advisory VLM availability follows the flag...
        self.assertFalse(container_off.resolve(Tokens.ADVISORY_VLM_PIPELINE).ready)
        self.assertTrue(container_on.resolve(Tokens.ADVISORY_VLM_PIPELINE).ready)
        # ...but the verdict-feeding multimodal pipeline is unchanged (never Kimi).
        for container in (container_off, container_on):
            self.assertIsInstance(
                container.resolve(Tokens.MULTIMODAL_DRAWING_PIPELINE),
                OcrFallbackMultimodalDrawingPipeline,
            )

        def verdict(container: object, tag: str) -> object:
            use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)
            report = use_case.execute(replace(request, request_id=f"offon-{tag}"))
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

    def test_llm_studio_flag_does_not_change_verdict_on_uc_path(self) -> None:
        """Yandex Studio / local OpenAI-compat advisory must also leave verdict byte-identical."""

        import json

        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.llm_advisory import DisabledLlmProvider
        from aerobim.infrastructure.adapters.openai_compat_llm_provider import (
            OpenAICompatLlmProvider,
        )
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
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
            llm_base_url="http://127.0.0.1:8000/v1",
            llm_provider="yandex-ai-studio",
            llm_model="qwen3-235b",
            llm_model_revision="yandex://ai-studio/qwen3-235b@test-pin",
            llm_api_key="test-key-not-for-prod",
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

        # Instant transport: wiring is under test; live Studio is operator Step 1.
        def _transport(_url: str, _headers: dict[str, str], _body: bytes) -> bytes:
            draft = {
                "title": "Advisory",
                "body": "Draft from deterministic finding.",
                "locale": "ru",
                "evidence_refs": ["deterministic"],
            }
            return json.dumps(
                {
                    "choices": [{"message": {"content": json.dumps(draft, ensure_ascii=False)}}],
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


if __name__ == "__main__":
    unittest.main()
