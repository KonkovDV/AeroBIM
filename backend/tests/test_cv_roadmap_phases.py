from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aerobim.domain.region_read_plan import plan_region_reads
from aerobim.infrastructure.adapters.heuristic_layout_region_detector import (
    HeuristicLayoutRegionDetector,
)
from aerobim.tools.run_vertical_slice import run_vertical_slice


class HeuristicLayoutRegionDetectorTests(unittest.TestCase):
    def test_emits_stamp_title_spec_dim_with_hitl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.pdf"
            path.write_bytes(b"%PDF-1.4\n")
            regions = HeuristicLayoutRegionDetector().detect(path, sheet_id="A-101")
        roles = {r.layout_role for r in regions}
        self.assertEqual(
            roles,
            {"content", "stamp", "title_block", "specification", "dimension_chain"},
        )
        self.assertTrue(all(r.modality == "detector" for r in regions))
        self.assertTrue(all(r.hitl_required for r in regions))
        self.assertTrue(all(r.coordinate_system == "normalized-0-1" for r in regions))

    def test_expected_blocked_roles_do_not_raise_unknown_coverage_alarm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.pdf"
            path.write_bytes(b"%PDF-1.4\n")
            regions = HeuristicLayoutRegionDetector().detect(path, sheet_id="A-101")
        plan = plan_region_reads(text_layer_present=False, regions=regions)
        # Only content is cloud-safe; others are expected blocked (not unknown).
        self.assertEqual(plan.excluded_unknown_role, 0)
        self.assertGreaterEqual(plan.excluded_by_role, 4)
        self.assertTrue(any(t.layout_role == "content" for t in plan.tasks))


class CvRoadmapSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[2]
        cls.manifest = cls.repo / "samples" / "demo" / "vertical-slice-2026-08-11" / "manifest.json"

    def test_slice_exposes_p0_p4_honest_phases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_vertical_slice(self.manifest, Path(tmp))
        phases = result["cv_phases"]
        self.assertEqual(phases["P0_ocr_raster"]["status"], "baseline_ready")
        self.assertIn("not engineering understanding", phases["P0_ocr_raster"]["claim"])
        self.assertIn(
            phases["P1_region_detector"]["status"],
            {"heuristic_baseline", "metrics_harness_ready"},
        )
        self.assertIn("stamp", phases["P1_region_detector"]["roles"])
        self.assertIn("specification", phases["P1_region_detector"]["roles"])
        self.assertIsNotNone(phases["P1_region_detector"].get("iou50_score"))
        self.assertEqual(phases["P1_region_detector"]["iou50_score"]["f1"], 1.0)
        self.assertEqual(phases["P2_symbol_spotting"]["status"], "vector_baseline_candidates")
        self.assertIsNotNone(phases["P2_symbol_spotting"].get("vector"))
        self.assertEqual(phases["P3_ifc_mapping"]["status"], "geo_tolerance_ready")
        geo = phases["P3_ifc_mapping"]["geo_confirm_demo"]
        self.assertTrue(geo["match_ok_guid_set"])
        self.assertTrue(geo["mismatch_clears_guid"])
        self.assertEqual(phases["P4_vlm_advisory"]["status"], "structured_candidate_ready")
        guard = phases["P4_vlm_advisory"]["advisory_guard"]
        self.assertTrue(guard["schema_conformant"])
        self.assertTrue(guard["passed_unchanged"])
        self.assertEqual(
            phases["P4_vlm_advisory"]["summary_passed_source"],
            "deterministic_engine_only",
        )
        # Evidence quality flags include OCR/text-layer honesty.
        ev = result["evidence"][0]
        self.assertIn("ocr_used", ev["quality_flags"])
        self.assertIn("text_layer_available", ev["quality_flags"])
        self.assertFalse(ev["quality_flags"]["cv_verified"])
        # Layout regions and IFC candidate links present.
        self.assertGreaterEqual(result["metrics"]["layout_region_count"], 5)
        self.assertGreaterEqual(result["metrics"]["ifc_candidate_link_count"], 1)
        self.assertFalse(result["summary"]["passed"])  # fixture has findings


if __name__ == "__main__":
    unittest.main()
