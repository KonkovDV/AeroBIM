from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


_CANONICAL_PACKS = [
    "project-package-baseline.json",
    "project-package-fire-compliance.json",
    "project-package-stress-multisource.json",
    "project-package-pilot-moscow-v1.json",
    "project-package-ablation-a0.json",
    "project-package-ablation-a3.json",
]


class PilotDeterministicReplayTests(unittest.TestCase):
    def test_canonical_benchmark_packs_produce_stable_issue_signatures(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        container = bootstrap_container(Settings.from_env())
        analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

        for pack_name in _CANONICAL_PACKS:
            pack_path = repo_root / "samples" / "benchmarks" / pack_name
            if not pack_path.exists():
                self.skipTest(f"Pack missing: {pack_name}")

            benchmark_pack = load_benchmark_pack(pack_path, repo_root_path=repo_root)
            signatures: list[tuple[tuple[str, str, str], ...]] = []
            for run_index in range(2):
                request = replace(
                    benchmark_pack.request,
                    request_id=f"deterministic-{pack_name}-{run_index:03d}",
                )
                report = analyze_use_case.execute(request)
                signature = tuple(
                    sorted(
                        (
                            issue.rule_id,
                            issue.category.value,
                            issue.severity.value,
                        )
                        for issue in report.issues
                    )
                )
                signatures.append(signature)
            self.assertEqual(signatures[0], signatures[1])

    def test_pilot_moscow_pack_produces_stable_issue_signature(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        if not pack_path.exists():
            self.skipTest("Pilot Moscow manifest missing")

        benchmark_pack = load_benchmark_pack(pack_path, repo_root_path=repo_root)
        container = bootstrap_container(Settings.from_env())
        analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

        signatures: list[tuple[tuple[str, str, str], ...]] = []
        for run_index in range(2):
            request = replace(
                benchmark_pack.request,
                request_id=f"deterministic-replay-{run_index:03d}",
            )
            report = analyze_use_case.execute(request)
            signature = tuple(
                sorted(
                    (
                        issue.rule_id,
                        issue.category.value,
                        issue.severity.value,
                    )
                    for issue in report.issues
                )
            )
            signatures.append(signature)

        self.assertEqual(signatures[0], signatures[1])
        self.assertGreater(len(signatures[0]), 0)

    def test_pilot_moscow_pack_structural_json_export_is_stable(self) -> None:
        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.infrastructure.di.bootstrap import bootstrap_container
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        pack_path = repo_root / "samples" / "benchmarks" / "project-package-pilot-moscow-v1.json"
        if not pack_path.exists():
            self.skipTest("Pilot Moscow manifest missing")

        benchmark_pack = load_benchmark_pack(pack_path, repo_root_path=repo_root)
        container = bootstrap_container(Settings.from_env())
        analyze_use_case = container.resolve(Tokens.ANALYZE_PROJECT_PACKAGE_USE_CASE)

        def issue_payload(report) -> list[dict[str, object]]:
            return [
                {
                    "rule_id": issue.rule_id,
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "conflict_kind": issue.conflict_kind.value if issue.conflict_kind else None,
                    "ifc_entity": issue.ifc_entity,
                    "property_name": issue.property_name,
                    "expected_value": issue.expected_value,
                    "observed_value": issue.observed_value,
                }
                for issue in sorted(report.issues, key=lambda item: item.rule_id)
            ]

        payloads: list[str] = []
        for run_index in range(2):
            request = replace(
                benchmark_pack.request,
                request_id=f"structural-json-{run_index:03d}",
            )
            report = analyze_use_case.execute(request)
            payloads.append(json.dumps(issue_payload(report), ensure_ascii=False, sort_keys=True))

        self.assertEqual(payloads[0], payloads[1])


if __name__ == "__main__":
    unittest.main()
