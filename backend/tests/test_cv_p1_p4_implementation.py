from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pdf_fixtures import write_text_pdf

from aerobim.domain.annotation_ifc_matching import (
    AnnotationIfcLink,
    confirm_link_against_spatial_index,
)
from aerobim.domain.pdf_vector_primitives import (
    extract_pdf_vector_primitives,
    propose_symbol_candidates_from_vectors,
)
from aerobim.domain.region_detection_metrics import (
    RegionLabel,
    score_region_detections,
)
from aerobim.domain.vlm_response_schema import validate_observations_response


class RegionDetectionMetricsTests(unittest.TestCase):
    def test_perfect_iou_match(self) -> None:
        preds = [
            RegionLabel("A-101", "stamp", (0.55, 0.82, 1.0, 1.0)),
            RegionLabel("A-101", "content", (0.0, 0.0, 1.0, 0.78)),
        ]
        labels = list(preds)
        score = score_region_detections(preds, labels, iou_threshold=0.5)
        self.assertEqual(score.tp, 2)
        self.assertEqual(score.fp, 0)
        self.assertEqual(score.fn, 0)
        self.assertEqual(score.f1, 1.0)
        self.assertIn("not product CV", score.claim_boundary)


class PdfVectorPrimitivesTests(unittest.TestCase):
    def test_extracts_text_from_vector_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pdf = write_text_pdf(Path(tmp) / "v.pdf", "WALL-01 thickness 150 mm")
            extraction = extract_pdf_vector_primitives(pdf)
        self.assertGreaterEqual(extraction.page_count, 1)
        self.assertGreaterEqual(extraction.as_dict()["primitive_counts"].get("text", 0), 1)
        self.assertIn("not CAD symbol spotting", extraction.claim)
        # Candidates may be empty on text-only PDFs — status remains honest.
        candidates = propose_symbol_candidates_from_vectors(extraction)
        self.assertIsInstance(candidates, list)


class IfcGeoToleranceTests(unittest.TestCase):
    class _Index:
        def __init__(self, box: tuple[float, float, float, float] | None) -> None:
            self._box = box

        def lookup(self, global_id: str) -> object | None:
            return object() if global_id == "G1" else None

        def bbox_xyxy_for(self, global_id: str) -> tuple[float, float, float, float] | None:
            return self._box if global_id == "G1" else None

    def test_geo_mismatch_clears_guid(self) -> None:
        link = AnnotationIfcLink(
            annotation_id="a1",
            sheet_id="A-101",
            target_ref="WALL-01",
            ifc_guid=None,
            match_basis="target_ref",
            confidence=0.5,
            evidence_ref="claimed_guid:G1#WALL-01",
        )
        ann_bbox = (10.0, 10.0, 50.0, 30.0)
        ok = confirm_link_against_spatial_index(
            link,
            self._Index(ann_bbox),
            annotation_bbox=ann_bbox,
            iou_tolerance=0.25,
        )
        bad = confirm_link_against_spatial_index(
            link,
            self._Index((0.0, 0.0, 1.0, 1.0)),
            annotation_bbox=ann_bbox,
            iou_tolerance=0.25,
        )
        self.assertEqual(ok.ifc_guid, "G1")
        self.assertIsNone(bad.ifc_guid)
        self.assertIn("geo_mismatch", bad.evidence_ref)


class VlmStructuredCandidateTests(unittest.TestCase):
    def test_candidate_class_schema_accepted(self) -> None:
        payload = {
            "readable": True,
            "observations": [
                {
                    "kind": "candidate_class",
                    "raw_value": "150",
                    "unit": "mm",
                    "ifc_target_hint": "WALL-01",
                    "bbox_rel": [0.1, 0.1, 0.2, 0.2],
                    "confidence": 0.7,
                }
            ],
        }
        result = validate_observations_response(payload)
        self.assertTrue(result.conformant, result.violations)


if __name__ == "__main__":
    unittest.main()
