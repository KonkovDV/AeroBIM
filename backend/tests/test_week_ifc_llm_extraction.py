from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class IfcSchemaSuiteBenchmarkTests(unittest.TestCase):
    def test_schema_suite_packs_load_with_ifc_schema(self) -> None:
        from aerobim.tools.benchmark_project_package import (
            load_benchmark_pack,
            schema_suite_pack_paths,
        )

        repo = Path(__file__).resolve().parents[2]
        packs = schema_suite_pack_paths(repo)
        self.assertEqual(len(packs), 3)
        schemas = set()
        for path in packs:
            pack = load_benchmark_pack(path, repo_root_path=repo)
            self.assertEqual(pack.corpus_kind, "fixture")
            self.assertIsNotNone(pack.ifc_schema)
            schemas.add(pack.ifc_schema)
            self.assertTrue(pack.request.ifc_path.exists())
        self.assertEqual(schemas, {"IFC2X3", "IFC4", "IFC4X3"})

    def test_group_by_schema_aggregates_pack_results(self) -> None:
        from aerobim.tools.benchmark_project_package import group_benchmark_results_by_schema

        grouped = group_benchmark_results_by_schema(
            [
                {
                    "ifc_schema": "IFC4",
                    "pack_id": "a",
                    "pack_path": "/tmp/a.json",
                    "ifc_sha256": "aa",
                    "summary": {"p50_ms": 10.0, "p95_ms": 10.0},
                    "measured_runs": [
                        {
                            "iteration": 1,
                            "request_id": "r1",
                            "elapsed_ms": 10.0,
                            "report_id": "x",
                            "issue_count": 2,
                            "requirement_count": 1,
                            "project_name": None,
                            "discipline": None,
                        }
                    ],
                },
                {
                    "ifc_schema": "IFC4",
                    "pack_id": "b",
                    "pack_path": "/tmp/b.json",
                    "ifc_sha256": "bb",
                    "summary": {"p50_ms": 20.0, "p95_ms": 20.0},
                    "measured_runs": [
                        {
                            "iteration": 1,
                            "request_id": "r2",
                            "elapsed_ms": 20.0,
                            "report_id": "y",
                            "issue_count": 3,
                            "requirement_count": 1,
                            "project_name": None,
                            "discipline": None,
                        }
                    ],
                },
            ]
        )
        self.assertEqual(grouped["group_by"], "schema")
        by_schema = grouped["by_schema"]
        assert isinstance(by_schema, dict)
        self.assertIn("IFC4", by_schema)
        metrics = by_schema["IFC4"]
        assert isinstance(metrics, dict)
        self.assertEqual(metrics["pack_count"], 2)
        timing = metrics["timing_ms"]
        assert isinstance(timing, dict)
        self.assertIn("p50_ms", timing)
        self.assertIn("p95_ms", timing)


class LlmExtractionPortTests(unittest.TestCase):
    def test_di_registers_extraction_ports(self) -> None:
        from dataclasses import replace

        from aerobim.core.config.settings import Settings
        from aerobim.core.di.tokens import Tokens
        from aerobim.domain.llm_extraction import ExtractionCandidate
        from aerobim.infrastructure.di.bootstrap import bootstrap_container

        with tempfile.TemporaryDirectory() as tmp:
            settings = replace(Settings.from_env(), storage_dir=Path(tmp))
            container = bootstrap_container(settings)
            regex = container.resolve(Tokens.LLM_EXTRACTION_REGEX)
            kimi = container.resolve(Tokens.LLM_EXTRACTION_KIMI)
            qwen = container.resolve(Tokens.LLM_EXTRACTION_QWEN)
            pipe = "SAM-R-001|IFCWALL|Pset_WallCommon|FireRating|REI60\n"
            candidates = regex.extract_candidates(pipe, source_id="t")
            self.assertTrue(candidates)
            self.assertIsInstance(candidates[0], ExtractionCandidate)
            self.assertTrue(candidates[0].evidence_refs)
            skipped_kimi = kimi.extract_candidates("текст без ключей", source_id="t")
            self.assertTrue(skipped_kimi)
            self.assertEqual(skipped_kimi[0].status, "skipped")
            skipped_qwen = qwen.extract_candidates("текст без ключей", source_id="t")
            self.assertEqual(skipped_qwen[0].status, "skipped")

    def test_evaluate_llm_extraction_mock_path(self) -> None:
        from aerobim.tools.evaluate_llm_extraction import evaluate_llm_extraction

        repo = Path(__file__).resolve().parents[2]
        corpus = repo / "samples" / "benchmarks" / "russian-aec-ground-truth.json"
        payload = evaluate_llm_extraction(corpus, write_evidence=False)
        self.assertEqual(payload["claim_level"], "fixture_only")
        self.assertFalse(payload["live_provider"])
        self.assertIn("regex", payload["summary"])
        self.assertIn("kimi", payload["summary"])
        self.assertIn("qwen", payload["summary"])
        self.assertIn("not established", payload["conclusion"].lower())

    def test_extraction_not_on_analyze_use_case_ctor(self) -> None:
        import inspect

        from aerobim.application.use_cases.analyze_project_package import (
            AnalyzeProjectPackageUseCase,
        )

        signature = inspect.signature(AnalyzeProjectPackageUseCase.__init__)
        param_names = set(signature.parameters)
        self.assertNotIn("llm_extraction", param_names)
        self.assertNotIn("llm_extraction_port", param_names)
        source = Path(inspect.getsourcefile(AnalyzeProjectPackageUseCase) or "")
        text = source.read_text(encoding="utf-8") if source.exists() else ""
        self.assertNotIn("LlmExtractionPort", text)
        self.assertNotIn("LLM_EXTRACTION", text)


class DwgFailClosedStillHolds(unittest.TestCase):
    def test_dwg_blocker_memo_exists(self) -> None:
        memo = Path(__file__).resolve().parents[2] / "docs" / "dwg-blocker-memo-2026-08.md"
        self.assertTrue(memo.is_file())
        text = memo.read_text(encoding="utf-8")
        self.assertIn("PILOT_OUT_OF_SCOPE", text)
        self.assertIn("ПП РФ 614", text)
        self.assertIn("CADSoftTools", text)
        self.assertIn("fail-closed", text.lower())


if __name__ == "__main__":
    unittest.main()
