from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aerobim.application.use_cases.analyze_project_package import AnalyzeProjectPackageUseCase
from aerobim.domain.models import (
    ComparisonOperator,
    DrawingAnnotation,
    DrawingSource,
    ParsedRequirement,
    ProblemZone,
    RequirementSource,
    RuleScope,
    Severity,
    SourceKind,
    ValidationIssue,
    ValidationReport,
    ValidationRequest,
)
from aerobim.infrastructure.adapters.template_remark_generator import TemplateRemarkGenerator


class FakeExtractor:
    def extract(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-001",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
            )
        ]


class FakeSynthesizer:
    def synthesize(self, _source: RequirementSource) -> list[ParsedRequirement]:
        return [
            ParsedRequirement(
                rule_id="REQ-DRW-001",
                ifc_entity="IFCWALL",
                rule_scope=RuleScope.DRAWING_ANNOTATION,
                target_ref="WALL-01",
                property_name="thickness",
                operator=ComparisonOperator.GREATER_OR_EQUAL,
                expected_value="200",
                unit="mm",
                source_kind=SourceKind.TECHNICAL_SPECIFICATION,
            )
        ]


class FakeDrawingAnalyzer:
    def analyze(self, _source: DrawingSource) -> list[DrawingAnnotation]:
        return [
            DrawingAnnotation(
                annotation_id="ANN-001",
                sheet_id="A-101",
                target_ref="WALL-01",
                measure_name="thickness",
                observed_value="150",
                unit="mm",
                problem_zone=ProblemZone(
                    sheet_id="A-101", page_number=1, x=10, y=20, width=100, height=50
                ),
            )
        ]


class FakeValidator:
    def validate(
        self, _ifc_path: Path, _requirements: list[ParsedRequirement]
    ) -> list[ValidationIssue]:
        return [
            ValidationIssue(
                rule_id="REQ-001",
                severity=Severity.ERROR,
                message="Property value mismatch",
                ifc_entity="IFCWALL",
                property_set="Pset_WallCommon",
                property_name="FireRating",
                expected_value="REI60",
                observed_value="REI30",
                element_guid="3s2Yw0ExampleGuid",
            )
        ]


class FakeStore:
    def __init__(self) -> None:
        self.saved_report_id: str | None = None

    def save(self, report: ValidationReport) -> str:
        self.saved_report_id = report.report_id
        return report.report_id


class AnalyzeProjectPackageUseCaseTests(unittest.TestCase):
    def test_execute_builds_multimodal_report_with_generated_remarks(self) -> None:
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-001",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                technical_spec_source=RequirementSource(
                    text="Лист A-101: толщина WALL-01 не менее 200 мм",
                    source_kind=SourceKind.TECHNICAL_SPECIFICATION,
                ),
                drawing_sources=(
                    DrawingSource(text="ANN-001|A-101|WALL-01|thickness|150|mm|1|10|20|100|50"),
                ),
            )
        )

        self.assertEqual(report.summary.requirement_count, 2)
        self.assertEqual(report.summary.issue_count, 2)
        self.assertEqual(report.summary.error_count, 2)
        self.assertEqual(report.summary.drawing_annotation_count, 1)
        self.assertEqual(report.summary.generated_remark_count, 2)
        self.assertEqual(len(report.drawing_annotations), 1)
        self.assertTrue(all(issue.remark is not None for issue in report.issues))
        self.assertEqual(store.saved_report_id, report.report_id)


class CalculationSourceTests(unittest.TestCase):
    """Tests that calculation_source feeds into synthesized requirements."""

    CALC_FIXTURE = (
        Path(__file__).resolve().parents[2] / "samples" / "calculations" / "area-requirement.txt"
    )

    def test_calculation_text_produces_synthesized_requirements(self) -> None:
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer as RealSynthesizer,
        )

        synthesizer = RealSynthesizer()
        source = RequirementSource(
            text=(
                "Помещение ГОС-001: площадь не менее 25 м2\n"
                "Wall ГОС-002 fire rating должна быть REI90"
            ),
            source_kind=SourceKind.CALCULATION,
        )
        rules = synthesizer.synthesize(source)
        self.assertEqual(len(rules), 2)
        rule_ids_lower = " ".join(r.rule_id for r in rules).lower()
        self.assertIn("area", rule_ids_lower)
        self.assertIn("fire-rating", rule_ids_lower)

    def test_calculation_fixture_file_produces_area_requirement(self) -> None:
        from aerobim.infrastructure.adapters.narrative_rule_synthesizer import (
            NarrativeRuleSynthesizer as RealSynthesizer,
        )

        if not self.CALC_FIXTURE.exists():
            self.skipTest("Calculation fixture not found")

        synthesizer = RealSynthesizer()
        source = RequirementSource(
            text="",
            path=self.CALC_FIXTURE,
            source_kind=SourceKind.CALCULATION,
        )
        rules = synthesizer.synthesize(source)
        self.assertGreaterEqual(len(rules), 1, "Fixture should produce at least 1 requirement")
        area_rules = [r for r in rules if "area" in r.rule_id.lower()]
        self.assertEqual(len(area_rules), 1)
        self.assertEqual(area_rules[0].expected_value, "25")

    def test_calculation_source_in_multimodal_use_case(self) -> None:
        """calculation_source is processed end-to-end by AnalyzeProjectPackageUseCase."""
        store = FakeStore()
        use_case = AnalyzeProjectPackageUseCase(
            requirement_extractor=FakeExtractor(),
            narrative_rule_synthesizer=FakeSynthesizer(),
            drawing_analyzer=FakeDrawingAnalyzer(),
            ifc_validator=FakeValidator(),
            remark_generator=TemplateRemarkGenerator(),
            audit_report_store=store,
        )

        report = use_case.execute(
            ValidationRequest(
                request_id="req-calc",
                ifc_path=Path("sample.ifc"),
                requirement_source=RequirementSource(
                    text="REQ-001|IFCWALL|Pset_WallCommon|FireRating|REI60"
                ),
                calculation_source=RequirementSource(
                    text="Помещение ГОС-001: площадь не менее 25 м2",
                    source_kind=SourceKind.CALCULATION,
                ),
            )
        )

        self.assertGreater(
            report.summary.requirement_count,
            1,
            "Should include synthesized requirement from calculation",
        )
        self.assertEqual(store.saved_report_id, report.report_id)


if __name__ == "__main__":
    unittest.main()
