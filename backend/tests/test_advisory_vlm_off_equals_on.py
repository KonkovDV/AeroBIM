"""Advisory OFF==ON invariant on the real AnalyzeProjectPackageUseCase path (§0.3/§7).

Toggling ``kimi_advisory_ready()`` must NOT change ``summary.passed`` or the
persisted verdict issues. The advisory VLM is a separate DI token deliberately
not consumed by the verdict path; this test is the regression guard that proves
the flag toggles advisory availability while the deterministic verdict is
byte-identical.
"""

from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
