from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    DrawingAnnotation,
    DrawingSource,
    FindingCategory,
    ParsedRequirement,
    RequirementSource,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class ConflictExtractor:
    """Returns a requirement that conflicts with the synthesizer's output."""

    def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-STR-001",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
                source_kind=SourceKind.STRUCTURED_TEXT,
            )
        ]


class ConflictSynthesizer:
    """Returns a requirement with a conflicting value from a different source."""

    def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-CALC-001",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI90",
                source_kind=SourceKind.CALCULATION,
            )
        ]


class NoOpDrawingAnalyzer:
    def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
        return []


class NoOpValidator:
    def validate(self, _ifc_path: Path, _reqs: list[ParsedRequirement]) -> list[ValidationIssue]:
        return []


class FakeStore:
    def __init__(self) -> None:
        self.saved_report_id: str | None = None
        self._reports: dict[str, ValidationReport] = {}

    def save(self, report: ValidationReport) -> str:
        self.saved_report_id = report.report_id
        self._reports[report.report_id] = report
        return report.report_id

    def get(self, report_id: str) -> ValidationReport | None:
        return self._reports.get(report_id)

    def list_reports(self) -> list:
        return []


class CrossDocumentContradictionTests(unittest.TestCase):
    def test_contradiction_between_structured_and_calculation_sources(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=ConflictExtractor(),
            narrative_rule_synthesizer=ConflictSynthesizer(),
            drawing_analyzer=NoOpDrawingAnalyzer(),
            ifc_validator=NoOpValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-cross-doc",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text="dummy"),
                calculation_source=RequirementSource(
                    text="Wall IfcWall fire rating must be REI90",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        cross_issues = [i for i in report.issues if i.category == FindingCategory.CROSS_DOCUMENT]
        self.assertGreaterEqual(
            len(cross_issues), 1, "Expected at least one cross-document contradiction"
        )

        issue = cross_issues[0]
        self.assertEqual(issue.severity, Severity.WARNING)
        self.assertIn("contradiction", issue.message.lower())
        self.assertIn("REI60", issue.message)
        self.assertIn("REI90", issue.message)

    def test_no_contradiction_when_values_agree(self) -> None:
        """Same value from different sources should not produce contradiction."""

        class AgreeSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return [
                    ParsedRequirement(
                        rule_id="REQ-CALC-002",
                        ifc_entity="IFCWALL",
                        property_set="Pset_WallCommon",
                        property_name="FireRating",
                        expected_value="REI60",
                        source_kind=SourceKind.CALCULATION,
                    )
                ]

        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=ConflictExtractor(),
            narrative_rule_synthesizer=AgreeSynthesizer(),
            drawing_analyzer=NoOpDrawingAnalyzer(),
            ifc_validator=NoOpValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-agree",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text="dummy"),
                calculation_source=RequirementSource(
                    text="Wall IfcWall fire rating must be REI60",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        cross_issues = [i for i in report.issues if i.category == FindingCategory.CROSS_DOCUMENT]
        self.assertEqual(len(cross_issues), 0, "No contradiction expected when values agree")

    def test_no_contradiction_when_numeric_values_match_after_unit_normalization(self) -> None:
        class MetricExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return [
                    ParsedRequirement(
                        rule_id="REQ-STR-002",
                        ifc_entity="IFCWALL",
                        property_set="Qto_WallBaseQuantities",
                        property_name="Width",
                        expected_value="3.0",
                        unit="m",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    )
                ]

        class MillimetreSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return [
                    ParsedRequirement(
                        rule_id="REQ-CALC-003",
                        ifc_entity="IFCWALL",
                        property_set="Qto_WallBaseQuantities",
                        property_name="Width",
                        expected_value="3000",
                        unit="mm",
                        source_kind=SourceKind.CALCULATION,
                    )
                ]

        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=MetricExtractor(),
            narrative_rule_synthesizer=MillimetreSynthesizer(),
            drawing_analyzer=NoOpDrawingAnalyzer(),
            ifc_validator=NoOpValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-numeric-unit-agree",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text="dummy"),
                calculation_source=RequirementSource(
                    text="Wall width is 3000 mm",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        cross_issues = [i for i in report.issues if i.category == FindingCategory.CROSS_DOCUMENT]
        self.assertEqual(
            len(cross_issues),
            0,
            "Equivalent values in m and mm should not produce a contradiction",
        )

    def test_no_contradiction_when_property_sets_differ(self) -> None:
        class DifferentPsetExtractor:
            def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return [
                    ParsedRequirement(
                        rule_id="REQ-STR-003",
                        ifc_entity="IFCWALL",
                        property_set="Pset_WallCommon",
                        property_name="FireRating",
                        expected_value="REI60",
                        source_kind=SourceKind.STRUCTURED_TEXT,
                    )
                ]

        class DifferentPsetSynthesizer:
            def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
                return [
                    ParsedRequirement(
                        rule_id="REQ-CALC-004",
                        ifc_entity="IFCWALL",
                        property_set="Pset_FireSafety",
                        property_name="FireRating",
                        expected_value="REI90",
                        source_kind=SourceKind.CALCULATION,
                    )
                ]

        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=DifferentPsetExtractor(),
            narrative_rule_synthesizer=DifferentPsetSynthesizer(),
            drawing_analyzer=NoOpDrawingAnalyzer(),
            ifc_validator=NoOpValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-pset-split",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(text="dummy"),
                calculation_source=RequirementSource(
                    text="Fire safety pset disagrees but should not be compared",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        cross_issues = [i for i in report.issues if i.category == FindingCategory.CROSS_DOCUMENT]
        self.assertEqual(
            len(cross_issues),
            0,
            "Requirements from different property sets should not be compared",
        )


if __name__ == "__main__":
    unittest.main()
