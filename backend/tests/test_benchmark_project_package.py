from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.domain.models import ValidationReport, ValidationSummary


class BenchmarkProjectPackageToolTests(unittest.TestCase):
    def test_repository_benchmark_manifests_load_with_real_fixtures(self) -> None:
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        repo_root = Path(__file__).resolve().parents[2]
        manifests = [
            repo_root / "samples" / "benchmarks" / "project-package-baseline.json",
            repo_root / "samples" / "benchmarks" / "project-package-fire-compliance.json",
        ]

        for manifest_path in manifests:
            benchmark_pack = load_benchmark_pack(manifest_path, repo_root_path=repo_root)
            self.assertTrue(benchmark_pack.pack_id)
            self.assertTrue(benchmark_pack.request.ifc_path.exists())
            self.assertIsNotNone(benchmark_pack.request.requirement_source.path)
            assert benchmark_pack.request.requirement_source.path is not None
            self.assertTrue(benchmark_pack.request.requirement_source.path.exists())

    def test_load_benchmark_pack_builds_request_relative_to_repo_root(self) -> None:
        from aerobim.tools.benchmark_project_package import load_benchmark_pack

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "samples" / "benchmarks").mkdir(parents=True)
            (root / "samples" / "ifc").mkdir(parents=True)
            (root / "samples" / "requirements").mkdir(parents=True)
            (root / "samples" / "drawings").mkdir(parents=True)
            (root / "samples" / "specifications").mkdir(parents=True)

            ifc_path = root / "samples" / "ifc" / "fixture.ifc"
            requirement_path = root / "samples" / "requirements" / "rules.txt"
            drawing_path = root / "samples" / "drawings" / "drawing.txt"
            spec_path = root / "samples" / "specifications" / "spec.txt"

            ifc_path.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
            requirement_path.write_text("REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60\n", encoding="utf-8")
            drawing_path.write_text("ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50\n", encoding="utf-8")
            spec_path.write_text("Wall fire rating must be REI60\n", encoding="utf-8")

            manifest_path = root / "samples" / "benchmarks" / "baseline.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "pack_id": "baseline",
                        "description": "baseline pack",
                        "project_name": "Residential Tower Alpha",
                        "discipline": "architecture",
                        "request": {
                            "ifc_path": "samples/ifc/fixture.ifc",
                            "requirement_path": "samples/requirements/rules.txt",
                            "technical_spec_path": "samples/specifications/spec.txt",
                            "drawings": [
                                {
                                    "path": "samples/drawings/drawing.txt",
                                    "sheet_id": "A-101",
                                    "format": "text",
                                }
                            ],
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            benchmark_pack = load_benchmark_pack(manifest_path, repo_root_path=root)

            self.assertEqual(benchmark_pack.pack_id, "baseline")
            self.assertEqual(benchmark_pack.request.project_name, "Residential Tower Alpha")
            self.assertEqual(benchmark_pack.request.discipline, "architecture")
            self.assertTrue(benchmark_pack.request.ifc_path.samefile(ifc_path))
            assert benchmark_pack.request.requirement_source.path is not None
            self.assertTrue(benchmark_pack.request.requirement_source.path.samefile(requirement_path))
            assert benchmark_pack.request.technical_spec_source is not None
            assert benchmark_pack.request.technical_spec_source.path is not None
            self.assertTrue(benchmark_pack.request.technical_spec_source.path.samefile(spec_path))
            self.assertEqual(len(benchmark_pack.request.drawing_sources), 1)
            assert benchmark_pack.request.drawing_sources[0].path is not None
            self.assertTrue(benchmark_pack.request.drawing_sources[0].path.samefile(drawing_path))

    def test_summarize_benchmark_runs_calculates_aggregate_metrics(self) -> None:
        from aerobim.tools.benchmark_project_package import summarize_benchmark_runs

        summary = summarize_benchmark_runs(
            [
                {"elapsed_ms": 100.0, "report_id": "a" * 32, "issue_count": 1, "requirement_count": 2},
                {"elapsed_ms": 300.0, "report_id": "b" * 32, "issue_count": 2, "requirement_count": 3},
            ]
        )

        self.assertEqual(summary["min_ms"], 100.0)
        self.assertEqual(summary["max_ms"], 300.0)
        self.assertEqual(summary["avg_ms"], 200.0)
        self.assertGreater(summary["reports_per_second"], 0)

    def test_run_benchmark_executes_warmups_and_measured_runs(self) -> None:
        from aerobim.domain.models import RequirementSource, ValidationRequest
        from aerobim.tools.benchmark_project_package import run_benchmark

        class _FakeAnalyzeUseCase:
            def __init__(self) -> None:
                self.calls = 0

            def execute(self, request: ValidationRequest) -> ValidationReport:
                self.calls += 1
                return ValidationReport(
                    report_id=f"{self.calls:032d}",
                    request_id=request.request_id,
                    ifc_path=request.ifc_path,
                    created_at="2026-04-14T12:00:00+00:00",
                    project_name=request.project_name,
                    discipline=request.discipline,
                    requirements=(),
                    issues=(),
                    summary=ValidationSummary(
                        requirement_count=0,
                        issue_count=0,
                        error_count=0,
                        warning_count=0,
                        passed=True,
                    ),
                )

        use_case = _FakeAnalyzeUseCase()
        request = ValidationRequest(
            request_id="bench-001",
            ifc_path=Path("sample.ifc"),
            requirement_source=RequirementSource(text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"),
            project_name="Residential Tower Alpha",
            discipline="architecture",
        )

        result = run_benchmark(use_case, request, iterations=2, warmup_iterations=1)

        self.assertEqual(use_case.calls, 3)
        self.assertEqual(result["iterations"], 2)
        self.assertEqual(result["warmup_iterations"], 1)
        self.assertEqual(len(result["measured_runs"]), 2)
        self.assertEqual(result["measured_runs"][0]["project_name"], "Residential Tower Alpha")
        self.assertEqual(result["measured_runs"][0]["discipline"], "architecture")


if __name__ == "__main__":
    unittest.main()