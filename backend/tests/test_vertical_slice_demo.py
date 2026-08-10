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
            html = (Path(tmp) / "report.html").read_text(encoding="utf-8")
            self.assertIn("WALL-01", html)
            self.assertIn("finding_id=", html.lower())
            self.assertIn("evidence_refs=", html.lower())
            self.assertIn(result["report_id"], html)


if __name__ == "__main__":
    unittest.main()
