from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aerobim.tools.measure_extent_clash_fixture import measure
from aerobim.tools.render_drawing_overlay_evidence import render_overlay


_REPO = Path(__file__).resolve().parents[2]


class ExtentClashFixtureMeasureTests(unittest.TestCase):
    def test_fixture_micro_perfect_on_intended_overlaps(self) -> None:
        ifc = _REPO / "samples" / "ifc" / "clash-extent-overlap-fixture.ifc"
        if not ifc.is_file():
            self.skipTest("extent clash fixture IFC missing")
        with tempfile.TemporaryDirectory() as tmp:
            status = measure(ifc_path=ifc, evidence_dir=Path(tmp))
        self.assertEqual(status["status"], "fixture_measured")
        self.assertEqual(status["claim_level"], "fixture_only")
        self.assertEqual(status["n_confirmed_clash_labels"], 6)
        micro = status["micro"]
        assert isinstance(micro, dict)
        self.assertEqual(micro["tp"], 6)
        self.assertEqual(micro["fp"], 0)
        self.assertEqual(micro["fn"], 0)
        self.assertEqual(micro["precision"], 1.0)
        self.assertEqual(micro["recall"], 1.0)

    def test_fixture_precision_recall_stays_non_customer(self) -> None:
        ifc = _REPO / "samples" / "ifc" / "clash-extent-overlap-fixture.ifc"
        if not ifc.is_file():
            self.skipTest("extent clash fixture IFC missing")
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp)
            measure(ifc_path=ifc, evidence_dir=evidence)
            pr = json.loads((evidence / "precision-recall.json").read_text(encoding="utf-8"))
        self.assertEqual(pr["claim_level"], "fixture_only")
        self.assertEqual(pr["corpus_kind"], "fixture")
        self.assertFalse(pr["publishable_protocol_gate"])
        self.assertFalse(pr["precision_claim"]["base_publishable"])
        self.assertFalse(pr["precision_claim"]["publishable"])
        self.assertIn("withheld", pr["precision_claim"]["render"])


class DrawingOverlayEvidenceTests(unittest.TestCase):
    def test_renders_png_with_zone(self) -> None:
        pdf = (
            _REPO
            / "samples"
            / "demo"
            / "vertical-slice-2026-08-11"
            / "techlab-a101-wall-thickness.pdf"
        )
        if not pdf.is_file():
            self.skipTest("vertical-slice PDF missing")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "overlay.png"
            meta = render_overlay(
                pdf_path=pdf,
                out_png=out,
                zone={"x": 72.0, "y": 62.0, "width": 150.0, "height": 14.0},
            )
            self.assertTrue(out.is_file())
            self.assertEqual(len(str(meta["sha256"])), 64)
            self.assertIn("not CV", str(meta["claim_boundary"]))


if __name__ == "__main__":
    unittest.main()
