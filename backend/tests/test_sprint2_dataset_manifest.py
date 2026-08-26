"""Sprint 2 dataset manifest contracts: determinism, provenance, claim lock."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[2]


class Sprint2DatasetManifestTests(unittest.TestCase):
    def test_two_exports_byte_identical(self) -> None:
        from aerobim.tools.export_sprint2_dataset_manifest import write_artifacts

        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            a = write_artifacts(repo=REPO, out_dir=Path(tmp_a))
            b = write_artifacts(repo=REPO, out_dir=Path(tmp_b))
            bytes_a = a["manifest"].read_bytes()
            bytes_b = b["manifest"].read_bytes()
            self.assertEqual(bytes_a, bytes_b)
            ha = hashlib.sha256(bytes_a).hexdigest()
            hb = hashlib.sha256(bytes_b).hexdigest()
            self.assertEqual(ha, hb)

    def test_provenance_synthetic_and_no_customer_claim(self) -> None:
        from aerobim.tools.export_sprint2_dataset_manifest import build_manifest

        manifest = build_manifest(REPO)
        self.assertEqual(manifest["claim_level"], "synthetic_only")
        self.assertIs(manifest["customer_precision_claim_publishable"], False)
        self.assertIs(manifest["customer_evidence"], False)
        self.assertEqual(manifest["checkpoint"], "NO_GO")
        self.assertIn("reproducibility_hash", manifest)
        self.assertGreaterEqual(len(manifest["mode_b_classes"]), 3)
        for case in manifest["cases"]:
            self.assertEqual(case["status"], "synthetic")
            self.assertEqual(case["claim_level"], "synthetic_only")
            self.assertIs(case["customer_precision_claim_publishable"], False)
            for field in (
                "case_id",
                "source_package",
                "expected_findings",
                "severity",
                "rule_id",
                "evidence_refs",
                "ground_truth_source",
                "generator",
                "seed",
                "schema_version",
                "sha256",
            ):
                self.assertIn(field, case, msg=f"missing {field} on {case.get('case_id')}")

    def test_no_train_test_identity_leakage(self) -> None:
        from aerobim.tools.export_sprint2_dataset_manifest import build_manifest

        manifest = build_manifest(REPO)
        ids = [c["case_id"] for c in manifest["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        # Same underlying GT defect must not share identical case_id across classes.
        by_class: dict[str, set[str]] = {}
        for case in manifest["cases"]:
            by_class.setdefault(str(case["case_class"]), set()).add(str(case["case_id"]))
        classes = list(by_class)
        for i, left in enumerate(classes):
            for right in classes[i + 1 :]:
                overlap = by_class[left] & by_class[right]
                self.assertFalse(overlap, msg=f"case_id overlap {left} vs {right}: {overlap}")

    def test_mode_a_inventory_no_download(self) -> None:
        from aerobim.tools.export_sprint2_dataset_manifest import build_mode_a_inventory

        inv = build_mode_a_inventory(REPO)
        self.assertIs(inv["download_performed"], False)
        self.assertEqual(inv["claim_level"], "synthetic_only")
        self.assertTrue(inv["sources"])


class Sprint2BaselineReportTests(unittest.TestCase):
    def test_baseline_writes_canonical_and_pdf_nonempty(self) -> None:
        from aerobim.tools.export_sprint2_dataset_manifest import write_artifacts
        from aerobim.tools.run_sprint2_synthetic_baseline import (
            run_baseline,
            write_reports,
        )

        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            paths = write_artifacts(repo=REPO, out_dir=tmp / "dataset")
            report = run_baseline(
                iterations=1,
                dataset_manifest_path=paths["manifest"],
            )
            self.assertEqual(report["claim_level"], "synthetic_only")
            self.assertIs(report["customer_precision_claim_publishable"], False)
            self.assertEqual(report["metrics"]["clashes_count"], 0)
            self.assertEqual(report["metrics"]["agreement"]["status"], "N/A")
            out = write_reports(
                report,
                out_json=tmp / "sprint2-baseline-report.json",
                out_md=tmp / "sprint2-baseline-report.md",
                out_pdf=tmp / "sprint2-baseline-report.pdf",
                out_html=tmp / "sprint2-baseline-report.html",
                also_dated=False,
            )
            self.assertGreater(out["pdf"].stat().st_size, 100)
            self.assertTrue(out["html"].is_file())
            loaded = json.loads(out["json"].read_text(encoding="utf-8"))
            self.assertEqual(loaded["claim_level"], "synthetic_only")

    def test_malformed_manifest_errors(self) -> None:
        from aerobim.tools.run_sprint2_synthetic_baseline import _load_dataset_manifest

        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            missing = tmp / "missing.json"
            with self.assertRaises(FileNotFoundError):
                _load_dataset_manifest(missing)
            bad = tmp / "bad.json"
            bad.write_text('{"artifact_type":"wrong","cases":[]}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                _load_dataset_manifest(bad)
            empty_cases = tmp / "empty.json"
            empty_cases.write_text(
                '{"artifact_type":"sprint2_dataset_manifest","cases":[]}\n',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                _load_dataset_manifest(empty_cases)


class Sprint2CustomerDocsTests(unittest.TestCase):
    def test_customer_pack_readme_stays_blocked(self) -> None:
        path = REPO / "samples" / "customer" / "README.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("NO_GO", text)
        self.assertIn("Do **not** commit", text)

    def test_customer_outreach_kitchen_is_unpublished(self) -> None:
        self.assertFalse((REPO / "docs" / "customer").exists())

    def test_baseline_banner_fields_when_written(self) -> None:
        from aerobim.tools.run_sprint2_synthetic_baseline import (
            run_baseline,
            write_reports,
        )

        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            report = run_baseline(iterations=1)
            self.assertIs(report["customer_accuracy_not_established"], True)
            self.assertIs(report["precision_claim_publishable"], False)
            out = write_reports(
                report,
                out_json=tmp / "sprint2-baseline-report.json",
                out_md=tmp / "sprint2-baseline-report.md",
                out_pdf=tmp / "sprint2-baseline-report.pdf",
                also_dated=False,
                also_brief_aliases=False,
            )
            md = out["md"].read_text(encoding="utf-8")
            self.assertIn("SYNTHETIC/FIXTURE ONLY", md)
            self.assertIn("CUSTOMER ACCURACY NOT ESTABLISHED", md)


class Sprint2LlmAdvisorySchemaTests(unittest.TestCase):
    def test_benchmark_schema_claim_and_no_verdict_mutation(self) -> None:
        from aerobim.tools.benchmark_llm_advisory import run_cases

        cases = REPO / "samples" / "benchmarks" / "llm-advisory" / "sprint-2-1-cases.json"
        report = run_cases(cases)
        self.assertIn(report["claim_level"], {"fixture_only", "synthetic_only"})
        self.assertIs(report["affects_summary_passed"], False)
        self.assertIs(report["customer_precision_claim_publishable"], False)
        self.assertIn("reproducibility", report)
        self.assertTrue(report["rows"])
        for row in report["rows"]:
            self.assertIn("latency_ms", row)
            self.assertIsNone(row.get("cost"))
            self.assertIn("json_validity", row)
            self.assertIn("agreement_with_deterministic", row)
            self.assertIn("hallucination_placeholder", row)
            self.assertIs(row["affects_summary_passed"], False)


if __name__ == "__main__":
    unittest.main()
