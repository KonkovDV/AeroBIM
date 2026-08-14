from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.run_vertical_slice import run_vertical_slice


class VerticalSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[2]
        cls.manifest = cls.repo / "samples" / "demo" / "vertical-slice-2026-08-11" / "manifest.json"
        cls.demo_pdf = (
            cls.repo
            / "samples"
            / "demo"
            / "vertical-slice-2026-08-11"
            / "techlab-a101-wall-thickness.pdf"
        )
        if not cls.demo_pdf.is_file():
            raise FileNotFoundError(f"Demo PDF missing: {cls.demo_pdf}")

    def _run(self, out: Path) -> dict:
        return run_vertical_slice(self.manifest, out)

    def test_extraction_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
            report = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))

            self.assertEqual(result["drawing_annotation_count"], 1)
            annotations = report["drawing_annotations"]
            self.assertEqual(len(annotations), 1)
            ann = annotations[0]
            self.assertEqual(ann["target_ref"], "WALL-01")
            self.assertEqual(ann["measure_name"], "thickness")
            self.assertEqual(ann["observed_value"], "150")
            self.assertEqual(ann["sheet_id"], "A-101")
            self.assertEqual(ann["source"], "raster-drawing-analyzer")
            pz = ann["problem_zone"]
            self.assertEqual(pz["page_number"], 1)
            self.assertGreater(pz["width"], 0)
            self.assertGreater(pz["height"], 0)

    def test_honest_coverage_and_claim_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
            counts = result["operator_status_counts"]
            self.assertGreaterEqual(counts.get("findings", 0), 1)
            self.assertGreaterEqual(counts.get("not_checked", 0), 1)
            self.assertIn("fixture_only", result["claim_boundary"])
            self.assertIn("not product CV", result["claim_boundary"])
            self.assertIn("not native DWG", result["claim_boundary"])

    def test_reproducible_findings_and_readonly_inputs(self) -> None:
        before = self.demo_pdf.read_bytes()
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            r1 = self._run(Path(tmp1))
            r2 = self._run(Path(tmp2))
            self.assertEqual(
                r1["reproducibility"]["finding_keys"],
                r2["reproducibility"]["finding_keys"],
            )
            self.assertEqual(
                [i["sha256"] for i in r1["inputs"] if "sha256" in i],
                [i["sha256"] for i in r2["inputs"] if "sha256" in i],
            )
        self.assertEqual(self.demo_pdf.read_bytes(), before)

    def test_json_html_artifacts_exist_and_contain_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
            self.assertTrue((Path(tmp) / "report.json").is_file())
            self.assertTrue((Path(tmp) / "report.html").is_file())
            self.assertTrue((Path(tmp) / "slice-summary.json").is_file())
            self.assertTrue((Path(tmp) / "LIMITATIONS.json").is_file())
            self.assertTrue((Path(tmp) / "findings.bcfzip").is_file())
            self.assertGreater((Path(tmp) / "findings.bcfzip").stat().st_size, 32)
            html = (Path(tmp) / "report.html").read_text(encoding="utf-8")
            self.assertIn("WALL-01", html)
            self.assertIn("finding_id=", html.lower())
            self.assertIn("evidence_refs=", html.lower())
            self.assertIn(result["report_id"], html)
            self.assertIn("kt2-overlay", html)
            self.assertIn("overlay-problem-zone.png", html)
            png = Path(tmp) / "overlay-problem-zone.png"
            self.assertTrue(png.is_file())
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertIsNotNone(result.get("overlay"))

    def test_evidence_envelope_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
            evidence = result["evidence"]
            self.assertEqual(len(evidence), 1)
            ev = evidence[0]
            self.assertEqual(ev["method"], "pdf_text_layer")
            self.assertEqual(
                ev["source_sha256"],
                "6aa1789a027f3a60be21bc68c26bb17440d4c54e827859c6268b590710125fcf",
            )
            self.assertEqual(ev["extracted_value"], "150")
            self.assertEqual(ev["normalized_value"], "150")
            self.assertEqual(ev["unit"], "mm")
            self.assertTrue(ev["quality_flags"]["heuristic_baseline"])
            self.assertFalse(ev["quality_flags"]["cv_verified"])
            self.assertIn("ocr_used", ev["quality_flags"])
            self.assertIn("text_layer_available", ev["quality_flags"])
            self.assertIn("evidence_hash", ev)

            metrics = result["metrics"]
            self.assertEqual(metrics["drawing_extraction_coverage"], 1.0)
            self.assertEqual(metrics["annotation_count"], 1)
            self.assertGreaterEqual(metrics["finding_count"], 1)
            self.assertGreaterEqual(metrics["not_checked_count"], 1)
            self.assertGreaterEqual(metrics["layout_region_count"], 5)


if __name__ == "__main__":
    unittest.main()
