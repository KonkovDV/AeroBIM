"""Tests for extraction quality benchmark harness."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.services.extraction_benchmark import (
    evaluate_fixture,
    run_extraction_benchmark,
)
from aerobim.domain.models import ParsedRequirement, SourceKind


class EvaluateFixtureTests(unittest.TestCase):
    def test_perfect_match(self) -> None:
        extracted = [
            ParsedRequirement(
                rule_id="R1",
                ifc_entity="IfcWall",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
                unit=None,
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        ]
        ground_truth = [
            {
                "rule_id": "R1",
                "ifc_entity": "IfcWall",
                "property_set": "Pset_WallCommon",
                "property_name": "FireRating",
                "expected_value": "REI60",
                "unit": None,
            }
        ]
        result = evaluate_fixture("fixture-1", extracted, ground_truth)
        self.assertEqual(result.true_positives, 1)
        self.assertEqual(result.false_positives, 0)
        self.assertEqual(result.false_negatives, 0)
        self.assertEqual(result.precision, 1.0)
        self.assertEqual(result.recall, 1.0)
        self.assertEqual(result.f1_score, 1.0)

    def test_false_positive_and_false_negative(self) -> None:
        extracted = [
            ParsedRequirement(
                rule_id="R1",
                ifc_entity="IfcWall",
                property_name="FireRating",
                expected_value="REI60",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        ]
        ground_truth = [
            {
                "rule_id": "R1",
                "ifc_entity": "IfcWall",
                "property_name": "Thickness",
                "expected_value": "200",
                "unit": "mm",
            }
        ]
        result = evaluate_fixture("fixture-2", extracted, ground_truth)
        self.assertEqual(result.true_positives, 0)
        self.assertEqual(result.false_positives, 1)
        self.assertEqual(result.false_negatives, 1)
        self.assertEqual(result.precision, 0.0)
        self.assertEqual(result.recall, 0.0)
        self.assertEqual(result.f1_score, 0.0)

    def test_unit_mismatch_counts_as_mismatch(self) -> None:
        extracted = [
            ParsedRequirement(
                rule_id="R1",
                ifc_entity="IfcWall",
                property_name="Thickness",
                expected_value="200",
                unit="mm",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        ]
        ground_truth = [
            {
                "rule_id": "R1",
                "ifc_entity": "IfcWall",
                "property_name": "Thickness",
                "expected_value": "200",
                "unit": "m",
            }
        ]
        result = evaluate_fixture("fixture-3", extracted, ground_truth)
        self.assertEqual(result.true_positives, 0)
        self.assertEqual(result.false_positives, 1)
        self.assertEqual(result.false_negatives, 1)

    def test_property_set_optional(self) -> None:
        extracted = [
            ParsedRequirement(
                rule_id="R1",
                ifc_entity="IfcWall",
                property_name="FireRating",
                expected_value="REI60",
                source_kind=SourceKind.STRUCTURED_TEXT,
            ),
        ]
        ground_truth = [
            {
                "rule_id": "R1",
                "ifc_entity": "IfcWall",
                "property_name": "FireRating",
                "expected_value": "REI60",
            }
        ]
        result = evaluate_fixture("fixture-4", extracted, ground_truth)
        self.assertEqual(result.true_positives, 1)


class RunBenchmarkIntegrationTests(unittest.TestCase):
    def test_runs_against_russian_aec_manifest(self) -> None:
        manifest_path = (
            Path(__file__).resolve().parents[2]
            / "samples"
            / "benchmarks"
            / "russian-aec-ground-truth.json"
        )
        if not manifest_path.exists():
            self.skipTest("Russian AEC ground-truth manifest not found")

        # Use a mock extractor that returns partial matches for fixture-1
        def extract_fn(path: Path):
            return [
                ParsedRequirement(
                    rule_id="R-WALL-THERMAL-01",
                    ifc_entity="IfcWall",
                    property_set="Pset_WallCommon",
                    property_name="ThermalTransmittance",
                    expected_value="3.5",
                    unit="m2K/W",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                ParsedRequirement(
                    rule_id="R-WALL-THERMAL-02",
                    ifc_entity="IfcWall",
                    property_set="Pset_WallCommon",
                    property_name="Thickness",
                    expected_value="380",
                    unit="mm",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
            ]

        summary = run_extraction_benchmark(manifest_path, extract_fn)
        self.assertEqual(len(summary.fixture_results), 10)
        self.assertGreaterEqual(summary.micro_precision, 0.0)
        self.assertGreaterEqual(summary.micro_recall, 0.0)
        # fixture-1 has 2 TP out of 5 GT (2 extracted, 5 ground-truth)
        fixture1 = [r for r in summary.fixture_results if r.fixture_id == "russian-wall-thermal"][0]
        self.assertEqual(fixture1.true_positives, 2)
        self.assertEqual(fixture1.false_positives, 0)
        self.assertEqual(fixture1.false_negatives, 3)


if __name__ == "__main__":
    unittest.main()
