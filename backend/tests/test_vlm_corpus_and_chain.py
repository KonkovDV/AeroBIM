"""P7 synthetic VLM corpus + P8 toolchain chain e2e (blind-spot wave).

P7: the corpus is *self-validating* — ground truth is the renderer input,
so extracting text back from the PDF must recover every GT string. P8: the
full artifact chain analyze → evidence bundle → detections export → labels
→ one-command harness must be schema-compatible end to end (the classic
seam where individually-tested tools drift apart). Claim boundary:
synthetic corpus / fixture chain only (RT-001).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pymupdf

from aerobim.tools.export_detections_from_report import build_detections_document
from aerobim.tools.generate_degraded_scans import generate_degraded_scans
from aerobim.tools.generate_vlm_fixture_corpus import generate_vlm_fixture_corpus
from aerobim.tools.run_pilot_harness import run_pilot_harness

_REPO = Path(__file__).resolve().parents[2]


class VlmFixtureCorpusTests(unittest.TestCase):
    def test_corpus_is_self_validating_against_rendered_text(self) -> None:
        """Every ground-truth string must be recoverable from its PDF —
        ground truth by construction, verified by construction."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            manifest = generate_vlm_fixture_corpus(output, sheet_count=3, seed=11)
            self.assertEqual(manifest["sheet_count"], 3)
            for sheet in manifest["sheets"]:
                gt = json.loads((output / sheet["ground_truth"]).read_text(encoding="utf-8"))
                document = pymupdf.open(output / sheet["pdf"])
                text = document[0].get_text()
                document.close()
                block = gt["t1_title_block"]
                for value in (
                    block["doc_code"],
                    block["sheet"],
                    block["revision"],
                    f"Stage {block['stage']}",
                ):
                    self.assertIn(value, text, msg=f"T1 {value}")
                for mark in gt["t2_marks"]:
                    self.assertIn(mark, text, msg=f"T2 {mark}")
                for row in gt["t3_table_rows"]:
                    self.assertIn(row["designation"], text, msg="T3 designation")
                    self.assertIn(
                        f"{row['position']} | {row['designation']} | {row['quantity']}",
                        text,
                        msg="T3 row",
                    )

    def test_ground_truth_deterministic_by_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = generate_vlm_fixture_corpus(Path(tmp) / "a", sheet_count=3, seed=7)
            second = generate_vlm_fixture_corpus(Path(tmp) / "b", sheet_count=3, seed=7)
            third = generate_vlm_fixture_corpus(Path(tmp) / "c", sheet_count=3, seed=8)
        gt_hashes = lambda manifest: [s["ground_truth_sha256"] for s in manifest["sheets"]]  # noqa: E731
        self.assertEqual(gt_hashes(first), gt_hashes(second))
        self.assertNotEqual(gt_hashes(first), gt_hashes(third))

    def test_t4_degradation_chains_on_corpus_sheet(self) -> None:
        """Corpus PDFs must feed generate_degraded_scans directly (T4)."""
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            manifest = generate_vlm_fixture_corpus(output, sheet_count=1, seed=3)
            sheet_pdf = output / manifest["sheets"][0]["pdf"]
            degraded = generate_degraded_scans(
                sheet_pdf,
                output / "degraded",
                dpi_variants=(96,),
                angles=(1.0,),
                noise_percents=(1.0,),
            )
        self.assertEqual(degraded["source"]["sha256"], manifest["sheets"][0]["pdf_sha256"])
        self.assertEqual(len(degraded["variants"]), 4)  # baseline + 3

    def test_invalid_sheet_count_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate_vlm_fixture_corpus(Path(tmp), sheet_count=0)


def _dedupe(records: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    unique: list[dict[str, str]] = []
    for record in records:
        key = tuple(sorted(record.items()))
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


class ToolchainChainE2ETests(unittest.TestCase):
    def test_bundle_report_chains_into_harness_with_perfect_match(self) -> None:
        """analyze → bundle report.json → detections export → auto-labels →
        run_pilot_harness. Labels are derived from the same findings, so the
        chain is healthy iff micro precision == recall == 1.0 — any schema
        or identity drift between the tools breaks the equality."""
        from aerobim.tools.export_evidence_bundle import export_evidence_bundle

        pack_path = _REPO / "samples" / "benchmarks" / "project-package-techlab-demo.json"
        if not pack_path.is_file():
            self.skipTest("techlab-demo pack missing")

        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp) / "bundle"
            export_evidence_bundle(
                pack_path=pack_path,
                output_dir=bundle_dir,
                storage_dir=Path(tmp) / "storage",
            )
            report_payload = json.loads((bundle_dir / "report.json").read_text(encoding="utf-8"))

            detections = build_detections_document(
                run_id="chain-e2e-run",
                case_id="CHAIN-01",
                report_payload=report_payload,
            )
            # Seam note: the exporter may emit duplicate identities (several
            # issues share rule_id+ref); harness rejects duplicates, so the
            # chain dedupes explicitly on both sides.
            findings = _dedupe(detections["cases"][0]["findings"])
            self.assertGreater(len(findings), 0, "demo pack must yield findings")
            detections["cases"][0]["findings"] = findings

            labels = {
                "schema_version": "1.0.0",
                "dataset_id": "chain-e2e-synthetic",
                "dataset_status": "synthetic",
                "scope_reference": "CHAIN-E2E-HARNESS-CONTRACT-ONLY",
                "cases": [
                    {
                        "case_id": "CHAIN-01",
                        "expected_findings": [
                            {**record, "adjudication_status": "confirmed"} for record in findings
                        ],
                    }
                ],
            }
            labels_path = Path(tmp) / "labels.json"
            detections_path = Path(tmp) / "detections.json"
            labels_path.write_text(json.dumps(labels), encoding="utf-8")
            detections_path.write_text(json.dumps(detections), encoding="utf-8")

            combined = run_pilot_harness(
                labels_path=labels_path,
                detections_path=detections_path,
            )

        micro = combined["precision"]["micro"]
        self.assertEqual(micro["precision"], 1.0)
        self.assertEqual(micro["recall"], 1.0)
        self.assertEqual(micro["fp"], 0)
        self.assertEqual(micro["fn"], 0)
        # Synthetic chain can never be publishable product accuracy.
        self.assertFalse(combined["publishable"])


if __name__ == "__main__":
    unittest.main()
